""" AutoServe module for combining the transcription module with the LLM agent."""

from source.agent.tools import (
    OrderTool,
    GetDetailedMenuTool,
    FindItemIdTool,
    MakeOrderCheckoutTool,
    GetOrderTool,
)

from source.audio.recorder import Recorder
from source.audio.transcriber import Transcriber

import os
from enum import Enum

from langchain.agents import AgentType, initialize_agent
from langchain.llms import vertexai

from google.cloud import aiplatform
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

from dotenv import load_dotenv

import asyncio

stop_recording = asyncio.Event() 

# want to start with it stopped.

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

        self.recorder = Recorder(trace=trace, verbose=verbose)
        self.transcriber = Transcriber()

        self.llm = vertexai.VertexAI(temperature=0)

        assert self.llm is not None, "LLM NOT INSTANTIATED"
        assert len(self.tools) > 0, "NEED AT LEAST ONE TOOL"

        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose,
        )

    async def handle_input(self):
        print(f"""
              Currently {self.state}. 
              Press r to record.
              Press s to stop recording.
              """)
        
        while True:
            user_input = await asyncio.to_thread(input, "")  # Take user input asynchronously
            if user_input == 'r':
                if self.state == State.RECORDING:
                    print("Already recording!")
                else:
                    print("Starting the recording.")
                    self.state=State.RECORDING
                    stop_recording.clear()

            elif user_input == 's':
                if self.state != State.RECORDING:
                    print("Not recording!")
                elif self.state == State.RECORDING:
                    print("Stopping the recording.")
                    stop_recording.set()
                    self.state = State.WAITING


    async def run(self):
        stop_recording.set()
        # Start both tasks and run them concurrently
        record_task = asyncio.create_task(self.recorder.record(stop_recording))
        input_task = asyncio.create_task(self.handle_input())

        await input_task
        await record_task

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