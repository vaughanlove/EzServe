""" 
AutoServe module for handling the event loop.

The AutoServe class is responsible for handling customer input 
to start/stop recording, and initiates the audio processing.
"""

import source.audio.translator as translator
import source.audio.transcriber as transcriber
#import source.audio.speaker as speaker
from source.agents.agentv2.agent import Agent # this import is gross

import sounddevice as sd
import soundfile as sf

import tempfile
import wave
import asyncio
import re
import sys
import os
import glob
import logging

from scipy.io.wavfile import write
from google.cloud import aiplatform
from google.cloud import texttospeech
from dotenv import load_dotenv

# Basic Logging
logging.basicConfig(level=logging.INFO)

# DEBUG Logging
# log = logging.getLogger("autoserve")
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Async input event flags
recording_flag = asyncio.Event()
processing_flag = asyncio.Event()
shutdown_flag = asyncio.Event()

# Instanstiate GCP TextToSpeechClient
client = texttospeech.TextToSpeechClient()

class AutoServe:
    """
    For handling state and managing i/o of the application.
    """
    agent = None

    async def run(self):
        # Start both tasks and run them concurrently
        record_task = asyncio.create_task(self.record())
        input_task = asyncio.create_task(self.handle_input())

        await input_task
        await record_task
        
    async def text_to_speech(self, text: str):
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request, select the language code ("en-US") and the ssml
        # voice gender ("neutral")
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-IN", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        ) 

        # write audio response to a temp output .wav file
        with tempfile.NamedTemporaryFile(dir="app/source/audio/audio_out/", delete=True, suffix='.wav') as temp_wav_file:
            temp_speaker_wav_path = temp_wav_file.name
            with wave.open(temp_speaker_wav_path, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(25000)
                wf.writeframes(response.audio_content)
                
            # async playback event
            playback = asyncio.Event()
            current_frame = 0
            # try and read from .wav file to playback
            try:
                with sf.SoundFile(temp_speaker_wav_path) as f:
                    data = f.read(always_2d=True)
                    
                    current_frame = 0
                    
                    def callback(outdata, frames, time, status):
                        nonlocal current_frame
                        if status:
                            print(status)
                        chunksize = min(len(data) - current_frame, frames)
                        outdata[:chunksize] = data[current_frame:current_frame + chunksize]
                        if chunksize < frames:
                            outdata[chunksize:] = 0
                            raise sd.CallbackStop()
                        current_frame += chunksize
                    # Sound device output stream
                    stream = sd.OutputStream(samplerate=25000, device=2, channels=data.shape[1], callback=callback, finished_callback=playback.set)
                    with stream:
                        await playback.wait()  # Wait until playback is finished
            except Exception as e:
                 print(f"An error occured: {e}")
        temp_wav_file.close()
        
    async def record(self):
        """
        Records the customer asynchronously, saves and performs operations on transcription, outputs Agent response as well as voice output.
        """
        # create tempfile for audio input
        with tempfile.NamedTemporaryFile(dir="app/source/audio/audio_in/", delete=True, suffix='.wav') as temp_wav_file:
            temp_wav_path = temp_wav_file.name
            try:
                with sf.SoundFile(temp_wav_path, mode='w', samplerate=self.samplerate,channels=self.channels, subtype=None) as file:
                    while True:
                        # check if recording event active
                        while not recording_flag.is_set():
                            if shutdown_flag.is_set():
                                sys.exit()
                            await asyncio.sleep(0.1)
                            
                        # async event loop for recording
                        loop = asyncio.get_event_loop()
                        record = asyncio.Event()
                        
                        # while recording event active, record input and write to .wav temp file
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

                        # Transcription of audio
                        transcript = transcriber.transcribe()

                        # Translation of transcription if needed based on language
                        language, result = translator.translate(transcript)
                        print(f"EzServe - Language Detected: {language}.")
                        print(f"EzServe - Translation: {result}.")
            
                        # Regex translation for formatted clean result
                        clean_result = re.sub(r"[^a-zA-Z0-9\s]", "", result)
                        
                        # Execute cleaned result in agent
                        agent_response = self.agent.run(clean_result)
                        print(f"EzServe - Console: {agent_response}")
                        
                        # Translate Agent Response
                        translated_response = translator.translate_to_language(agent_response, language)
                        print(f"EzServe - Translated Response: {translated_response}")
                        
                        print("<***> VIRTUAL SPEAKER <***>")
                        # Asyncronous call speaker
                        await self.text_to_speech(translated_response)
                        #speaker.text_to_speech(translated_response)
                        
                        # Clear processing flag and final customer transcription
                        processing_flag.clear()
                        file.truncate(0)
            except Exception as e:
                print(f"An error occured: {e}")
        # Close tempfile I/O
        temp_wav_file.close()

    async def handle_input(self):
        """ 
        Handle customer input using async events 
        """
        print("""
              Press r to record.
              Press s to stop recording.
              Press k to kill.
              """)
        while True:
            # Take customer input asynchronously
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
        """ 
        Load environment variables from .env file.
        """
        load_dotenv()  
        assert os.getenv("GOOGLE_PROJECT_ID") is not None, "MISSING GOOGLE_PROJECT_ID"
        assert os.getenv("LOCATION") is not None, "MISSING LOCATION"
        assert os.getenv("API_KEY") is not None, "MISSING API_KEY"
        os.environ["LANGCHAIN_TRACING"] = "false" if not trace else "true"

    def _setup_gcloud(self) -> None:
        """
        Authenticate with gcloud.
        """
        self.google_project_id = os.getenv("GOOGLE_PROJECT_ID")
        assert self.google_project_id is not None, "MISSING GOOGLE PROJECT ID"
        aiplatform.init(project=self.google_project_id, location="us-central1")

    def __init__(self, trace=False, verbose=True) -> bool:
        """ 
        Load env vars, setup gcloud, declare audio params, and instantiate Agent. 
        """
        self._load_env_vars(trace)
        self._setup_gcloud()
        
        self.channels = 1
        self.samplerate = 44100
        self.chunk = 1024

        self.agent = Agent(verbose=True)
