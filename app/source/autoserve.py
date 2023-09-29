""" 
AutoServe module for handling the event loop.

The AutoServe class is responsible for handling user input 
to start/stop recording, and initiates the audio processing.
"""

import source.audio.translator as translator
import source.audio.transcriber as transcriber
from source.agent.square_client import SquareClient

import pyaudio
import wave
import asyncio
import re
import sys
import os

from google.cloud import aiplatform

from dotenv import load_dotenv

recording_flag = asyncio.Event()
processing_flag = asyncio.Event()
shutdown_flag = asyncio.Event()

class AutoServe:
    """
    For handling state and managing i/o of the application.
    """
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
        """
        Opens audio stream and awaits a stop flag.
        Once stopped, sets the processing flag and initiates the audio processing.
        """
        while True:
            while not recording_flag.is_set():
                if shutdown_flag.is_set():
                    sys.exit()
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

            while recording_flag.is_set():
                data = stream.read(self.chunk)
                frames.append(data)
                # 1 / hz = seconds/sample.
                await asyncio.sleep(1 / self.rate)

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

            # clear the recording flag for next i/o
            recording_flag.clear()
            # set the processing_flag to block any initiate recording inputs.
            processing_flag.set()

            # do the transcription
            transcript = transcriber.transcribe()

            result = translator.translate(transcript)
            clean_result = re.sub(r"[^a-zA-Z0-9\s]", "", result)

            agent_response = self.agent.run(clean_result)
            # this is where we speech to text the agent_response.
            # clear the processing_flag to allow new recordings
            processing_flag.clear()

    async def handle_input(self):
        print("""
              Press r to record.
              Press s to stop recording.
              Press k to kill.
              """)
        while True:
            # Take user input asynchronously
            user_input = await asyncio.to_thread(input, "")
            if user_input == "k":
                shutdown_flag.set()
                break
            elif user_input == "r":
                if recording_flag.is_set():
                    print("Already recording!")
                elif processing_flag.is_set():
                    print("Hold on, still processing the last message.")
                elif not processing_flag.is_set() and not recording_flag.is_set():
                    print("Starting the recording.")
                    recording_flag.set()

            elif user_input == "s":
                if recording_flag.is_set():
                    print("Stopping recording!")
                    recording_flag.clear()

                elif processing_flag.is_set():
                    print("Wait for the last message to finish processing.")

    def _load_env_vars(self, trace: bool) -> None:
        load_dotenv()  # load environment variables from .env file
        assert os.getenv("GOOGLE_PROJECT_ID") is not None, "MISSING GOOGLE_PROJECT_ID"
        assert os.getenv("LOCATION") is not None, "MISSING LOCATION"
        assert os.getenv("API_KEY") is not None, "MISSING API_KEY"
        os.environ["LANGCHAIN_TRACING"] = "false" if not trace else "true"

    def _setup_gcloud(self) -> None:
        """Authenticate w/ gcloud"""
        self.google_project_id = os.getenv("GOOGLE_PROJECT_ID")
        assert self.google_project_id is not None, "MISSING GOOGLE PROJECT ID"
        aiplatform.init(project=self.google_project_id, location="us-central1")

    def __init__(self, trace=False, verbose=True) -> bool:
        self._load_env_vars(trace)
        self._setup_gcloud()

        # pyaudio settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024

        self.agent = SquareClient(verbose=verbose)
    