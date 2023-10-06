""" 
AutoServe module for handling the event loop.

The AutoServe class is responsible for handling user input 
to start/stop recording, and initiates the audio processing.
"""

import source.audio.translator as translator
import source.audio.transcriber as transcriber
import source.audio.speaker as speaker
from source.agents.agentv2.agent import Agent # this import is gross

import tempfile
import sounddevice as sd
from scipy.io.wavfile import write
import soundfile as sf

import asyncio
import re
import sys
import os
import glob
import logging

from google.cloud import aiplatform

from dotenv import load_dotenv

log = logging.getLogger("autoserve")
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

recording_flag = asyncio.Event()
processing_flag = asyncio.Event()
shutdown_flag = asyncio.Event()

class AutoServe:
    """
    For handling state and managing i/o of the application.
    """
    history = []
    transcribed_string = None

    agent = None
    llm = None

    async def run(self):
        # Start both tasks and run them concurrently
        record_task = asyncio.create_task(self.record())
        input_task = asyncio.create_task(self.handle_input())

        await input_task
        await record_task

    async def record(self):
        #WAVE_OUTPUT_FILENAME = "app/tmp/audio.wav" --tempfile.mktemp(prefix='audio_input', suffix='.wav', dir='') -'/home/dom/Desktop/autoserve/EzServe/app/audio_input.wav'
        with sf.SoundFile(tempfile.NamedTemporaryFile(dir="app/", delete=True, suffix='.wav'), mode='x', samplerate=self.samplerate,channels=self.channels, subtype=None) as file:
            while True:
                while not recording_flag.is_set():
                    if shutdown_flag.is_set():
                        sys.exit()
                    await asyncio.sleep(0.1)
                    
                loop = asyncio.get_event_loop()
                record = asyncio.Event()
                
                while recording_flag.is_set():
                    def callback(indata, frame_count, time_info, status):
                            if status:
                                print(status)
                            if not recording_flag.is_set():
                                loop.call_soon_threadsafe(record.set)
                                raise sd.CallbackStop
                            file.write(indata)
                    with sd.InputStream(samplerate=self.samplerate, device=None,channels=self.channels, callback=callback):
                        await record.wait()
				
				# clear the recording flag for next i/o
                recording_flag.clear()
                record.clear()
                
                # set the processing_flag to block any initiate recording inputs.
                processing_flag.set()

                # do the transcription
                transcript = transcriber.transcribe()

                language, result = translator.translate(transcript)
                clean_result = re.sub(r"[^a-zA-Z0-9\s]", "", result)

                print("detected language: " + language)

                agent_response = self.agent.run(clean_result)

                print("agent response: " + agent_response)
                print("SPEAKER")
                #speaker.text_to_speech(agent_response)
                # playback_task = asyncio.create_task(speaker.text_to_speech(agent_response))
                # await playback_task
                translated_response = translator.translate_to_language(agent_response, language)
                print(translated_response)
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

        self.channels = 1
        self.samplerate = 44100
        self.chunk = 1024

        self.agent = Agent(verbose=True)
