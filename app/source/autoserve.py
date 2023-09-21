""" AutoServe module for combining the transcription module with the LLM agent."""

from source.audio.translator import Translator
from source.audio.transcriber import Transcriber
from source.agent.square_client import SquareClient
from source.agent.tools import (
    OrderTool,
    GetDetailedMenuTool,
    FindItemIdTool,
    MakeOrderCheckoutTool,
    GetOrderTool,
)

import pyaudio
import wave
import asyncio
import re
import os

from langchain.agents import AgentType, initialize_agent
from langchain.llms import vertexai

from google.cloud import aiplatform


from dotenv import load_dotenv

recording_flag = asyncio.Event()
processing_flag = asyncio.Event()
shutdown_flag = asyncio.Event()

class AutoServe:
    """For managing state."""
    history = []
    transcribed_string = None

    WAVE_OUTPUT_FILENAME = "app/tmp/audio_file.wav"
    agent = None
    llm = None
    
    async def run(self):
        # Start both tasks and run them concurrently
        record_task = asyncio.create_task(self.record())
        input_task = asyncio.create_task(self.handle_input())

        await input_task
        await record_task
        
    async def record(self):
        """opens audio stream and writes to wav file till stopped"""

        while True:
            
            while not recording_flag.is_set():
                await asyncio.sleep(0.05)

            p = pyaudio.PyAudio()

            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )
    
            frames = []

            while recording_flag.is_set(): #mac keyboard work-around
                data = stream.read(self.chunk)
                frames.append(data)

                await asyncio.sleep(1 / 44100)  # This is hack but 1/ hz = seconds/sample and she works.

            # Close and terminate the stream
            stream.stop_stream()
            stream.close()
            sample_width = p.get_sample_size(self.format)
            p.terminate()

            # Save the audio data as a .wav file
            with wave.open(self.WAVE_OUTPUT_FILENAME, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(self.rate)
                wf.writeframes(b"".join(frames))
                wf.close()

            recording_flag.clear()
            processing_flag.set()

            # do the transcription
            transcript = self.t.transcribe()

            result = self.translator.translate(transcript)
            
            clean_result = re.sub(r'[^a-zA-Z0-9\s]', '', result)

            #print("translation: " + result)
            #print("clean translation: " + clean_result)

            agent_response = self.agent.run(clean_result)
            print("AGENT: " + agent_response)

            processing_flag.clear()

    async def handle_input(self):
        print("""
              Press r to record.
              Press s to stop recording.
              """)
        
        while True:
            user_input = await asyncio.to_thread(input, "")  # Take user input asynchronously
            if user_input == 'r':

                if recording_flag.is_set():
                    print("Already recording!")

                elif processing_flag.is_set():
                    print("Hold on, still processing the last message.")
                
                elif not processing_flag.is_set() and not recording_flag.is_set():
                    print("Starting the recording.")
                    recording_flag.set()

            elif user_input == 's':
                if recording_flag.is_set():
                    print("Stopping recording!")
                    recording_flag.clear()

                elif processing_flag.is_set():
                    print("Recording is already stopped. Please wait for the last message to be processed.")

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

    def __init__(self, trace=False, verbose=True) -> bool:
        self._load_env_vars(trace)
        self._setup_gcloud()

        tools = [
            GetDetailedMenuTool(),
            FindItemIdTool(),
            OrderTool(),
            MakeOrderCheckoutTool(),
            GetOrderTool(),
        ]

        self.transcriber = Transcriber()

        self.llm = vertexai.VertexAI(temperature=0)

        assert self.llm is not None, "LLM NOT INSTANTIATED"
        assert len(self.tools) > 0, "NEED AT LEAST ONE TOOL"

        # pyaudio settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024

        self.recording = True

        self.t = Transcriber()
        self.translator = Translator()
        self.agent = SquareClient(trace=trace, verbose=verbose)

        self.agent = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose,
        )