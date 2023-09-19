""" AutoServe module for combining the transcription module with the LLM agent."""

from source.agent.tools import (
    OrderTool,
    GetDetailedMenuTool,
    FindItemIdTool,
    MakeOrderCheckoutTool,
    GetOrderTool,
)

from source.audio.recorder import Recorder

import os
from enum import Enum

from langchain.agents import AgentType, initialize_agent
from langchain.llms import vertexai

from google.cloud import aiplatform
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

from dotenv import load_dotenv
import pyaudio
import wave

import asyncio

class State(Enum):
    RECORDING = 1
    PROCESSING = 2
    WAITING = 3

class AutoServe:
    """For managing state."""
    state = State.WAITING

    history = []
    transcribed_string = None
    WAVE_OUTPUT_FILENAME = "app/tmp/audio_file.wav"

    agent = None
    llm = None
    tools = [
        GetDetailedMenuTool(),
        FindItemIdTool(),
        OrderTool(),
        MakeOrderCheckoutTool(),
        GetOrderTool(),
    ]

    def __init__(self, trace=False, verbose=True) -> bool:
        self._load_env_vars(trace)
        self._setup_gcloud()

        self.recorder = Recorder()

        self.llm = vertexai.VertexAI(temperature=0)

        assert self.llm is not None, "LLM NOT INSTANTIATED"
        assert len(self.tools) > 0, "NEED AT LEAST ONE TOOL"

        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose,
        )

    async def run(self):
        print("starting async record")
        # Start both tasks and run them concurrently
        recordTask = asyncio.create_task(self.recorder.start())

        # here we want to listen for a flag being set when self.recorder finishes a recording.
        # when that flag is initiated, the transcriber() should be called and subsequently 
        # process() should be called.

        await recordTask


    def process(self):
        self.state = State.PROCESSING
        print("Start processing")
        client = SpeechClient()

        # Reads a file as bytes
        with open(self.WAVE_OUTPUT_FILENAME, "rb") as f:
            content = f.read()

        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="short",
        )

        project_id = os.getenv("SPEECH_PROJECT_ID")
        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{project_id}/locations/global/recognizers/_",
            config=config,
            content=content,
        )

        # Transcribes the audio into text
        response = client.recognize(request=request)

        print("TRANSCRIPTION: " + response.results[0].alternatives[0].transcript)
        # for result in response.results:
        #    print(f"Transcript: {result.alternatives[0].transcript}")

        agent_response = self.agent.run(response.results[0].alternatives[0].transcript)
        self.state = State.WAITING
        return agent_response

    def stop(self) -> None:
        self.state = State.PROCESSING

        # do the speech=> text and load text into member variable

    def get_state(self) -> State:
        return self.state

    def _load_env_vars(self, trace: bool) -> None:
        # load environment variables from .env file
        load_dotenv()

        assert os.getenv("GOOGLE_PROJECT_ID") is not None, "MISSING GOOGLE_PROJECT_ID"
        assert os.getenv("LOCATION") is not None, "MISSING LOCATION"
        assert os.getenv("API_KEY") is not None, "MISSING API_KEY"

        # trace langchain execution
        os.environ["LANGCHAIN_TRACING"] = "false" if not trace else "true"

        # Device presets.
        # More info at https://developer.squareup.com/docs/devtools/sandbox/testing
        device_id_checkout_success="9fa747a2-25ff-48ee-b078-04381f7c828f"
        device_id_checkout_success_tip = "22cd266c-6246-4c06-9983-67f0c26346b0"
        device_id_checkout_success_gc = "4mp4e78c-88ed-4d55-a269-8008dfe14e9"
        device_id_checkout_failure_buyer_cancel = "841100b9-ee60-4537-9bcf-e30b2ba5e215"

        # set what device ID to use
        os.environ["DEVICE"] = device_id_checkout_success_tip

    def _setup_gcloud(self) -> None:
        """Authenticate w/ gcloud"""
        google_project_id = os.getenv(
            "GOOGLE_PROJECT_ID"
        )  # ie, confident-jackle-123456
        aiplatform.init(project=google_project_id, location="us-central1")

    def _load_tools(self) -> None:
        """Load in tools module"""
        pass