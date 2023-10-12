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
import threading
import asyncio
import re
import sys
import os
import logging
import json

from scipy.io.wavfile import write
from google.cloud import aiplatform
from google.cloud import texttospeech
from dotenv import load_dotenv

# Basic Logging
#logging.basicConfig(level=logging.INFO)

# DEBUG Logging
log = logging.getLogger("autoserve")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Async input event flags
recording_flag = asyncio.Event()
failed_record_flag = asyncio.Event()
failed_order_flag = asyncio.Event()
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
        execution_task = asyncio.create_task(self.order_execution())
        input_task = asyncio.create_task(self.handle_input())

        await input_task
        await execution_task
	
    def text_to_speech(self, path, text: str):
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request, select the language code ("en-US") and the ssml
        # voice gender ("neutral")
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
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
        with tempfile.NamedTemporaryFile(dir=path, delete=True, suffix='.wav') as temp_wav_file:
            temp_speaker_wav_path = temp_wav_file.name
            with wave.open(temp_speaker_wav_path, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(25000)
                wf.writeframes(response.audio_content)
                
            # async playback event
            playback = threading.Event()
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
                    stream = sd.OutputStream(samplerate=25000, device=0, channels=data.shape[1], callback=callback, finished_callback=playback.set)
                    with stream:
                        print("about to wait")
                        playback.wait()  # Wait until playback is finished
                        print("playback here")
            except Exception as e:
                 print(f"An error occured: {e}")
        temp_wav_file.close()
        
    async def record(self, path, event, **kwargs):
	# create tempfile for audio input
        with tempfile.NamedTemporaryFile(dir=path, delete=True, suffix='.wav') as temp_wav_file:
            temp_wav_path = temp_wav_file.name
            try:
                with sf.SoundFile(temp_wav_path, mode='w', samplerate=self.samplerate,channels=self.channels, subtype=None) as file:
                    while True:
                        # check if recording event active
                        while not event.is_set():
                            if shutdown_flag.is_set():
                                sys.exit()
                            await asyncio.sleep(0.1)
                            
                        # async event loop for recording
                        loop = asyncio.get_event_loop()
                        record = asyncio.Event()
                        
                        # while recording event active, record input and write to .wav temp file
                        while event.is_set():
                            def callback(indata, frame_count, time_info, status):
                                    if status:
                                        print(status)
                                    if not event.is_set():
                                        loop.call_soon_threadsafe(record.set)
                                        raise sd.CallbackStop
                                    file.write(indata)
                            with sd.InputStream(samplerate=self.samplerate, device=None,channels=self.channels, callback=callback):
                                await record.wait()
                        
                        # clear the recording flag for next i/o
                        event.clear()
                        record.clear()
                        
                        # set the processing_flag to block any initiate recording inputs.
                        processing_flag.set()

                        # Transcription of audio
                        transcript = transcriber.transcribe(temp_wav_path)

                        # Translation of transcription if needed based on language
                        language, result = translator.translate(transcript)
            
                        # Regex translation for formatted clean result
                        clean_result = re.sub(r"[^a-zA-Z0-9\s]", "", result)
                        
                        # Execute cleaned result in agent
                        agent_response = self.agent.run(clean_result)
                        
                        file.truncate(0)
                        return agent_response, language
            except Exception as e:
                print(f"An error occured: {e}")
        # Close tempfile I/O
        temp_wav_file.close()
		
                
    def failed_order_execution(self, item):
        """
        Records the customer asynchronously, saves and performs operations on transcription, outputs Agent response as well as voice output.
        """        
        agent_response, language = await self.record("app/source/audio/human_input_in/", recording_flag)
        
        # note this execution is item by item, there should not be multiple items.
        # should probably do a check to ensure there arn't more than 1 failed_order in failed orders
        failed_orders = []
        resp = agent_response.split("Failed Orders:")[0].strip()
        print(resp)
        try:
            failed_orders = json.loads(agent_response.split("Failed Orders:")[-1].strip())
            print(f"\nFailed orders: {failed_orders}\n {type(failed_orders)} \n")
        except:
            print("there were no failed orders")
            
        if len(failed_orders) > 0:
            if failed_orders[0][0]['error_type'] == "MISSING_ITEM":
                self.text_to_speech("app/source/audio/audio_out/", f"Sorry, {failed_orders[0][0]['name']} is not on our menu.")
            elif failed_orders[0][0]['error_type'] == "SCORE_MATCH":
                self.text_to_speech("app/source/audio/audio_out/", f"Sorry, we still arn't sure what you want.")
                self.failed_order_execution(item)
            elif failed_orders[0][0]['error_type'] == "SQUARE_CALL":
                self.text_to_speech("app/source/audio/audio_out/", f"Something strange happened on Square's end. We are looking into it.")
        
        # Translate Agent Response
        translated_response = translator.translate_to_language(resp, language)
        
        print(f"(failed_order_execution) - translated response: {translated_response}")
        # Asyncronous call speaker
        self.text_to_speech("app/source/audio/audio_out/", translated_response)
        
        # Clear processing flag and final customer transcription
        processing_flag.clear()
	
    async def order_execution(self):
        """
        Records the customer asynchronously, saves and performs operations on transcription, outputs Agent response as well as voice output.
        """
        loop = asyncio.get_event_loop()
        while not shutdown_flag.is_set():
            agent_response, language = await self.record("app/source/audio/audio_in/", recording_flag)
            
            failed_orders = []
            resp = agent_response.split("Failed Orders:")[0].strip()
            print(resp)
            try:
                failed_orders = json.loads(agent_response.split("Failed Orders:")[-1].strip())
                print(f"\nFailed orders: {failed_orders}\n {type(failed_orders)} \n")
            except:
                print("there were no failed orders")    
            # Translate Agent Response
            translated_response = translator.translate_to_language(resp, language)
            
            # Asyncronous call speaker
            print(f"\n(order_execution) - translated response: {translated_response}\n" )

            self.text_to_speech("app/source/audio/audio_out/", translated_response)
            # initial processing done.
            processing_flag.clear()
            
            # if there was a failed order, iterate through 
            for item in failed_orders: 
                if item[0]['error_type'] == "MISSING_ITEM":
                    self.text_to_speech("app/source/audio/audio_out/", f"Sorry, {item[0]['name']} is not on our menu.")
                elif item[0]['error_type'] == "SCORE_MATCH":
                    self.text_to_speech("app/source/audio/audio_out/", f"We arn't sure if you wanted a {item[0]['name']} or a {item[1]['name']}, could you specify?")
                    self.failed_order_execution(item)
                elif item[0]['error_type'] == "SQUARE_CALL":
                    self.text_to_speech("app/source/audio/audio_out/", f"Something strange happened on Square's end. We are looking into it.")
            
            self.text_to_speech("app/source/audio/audio_out/", "Feel free to continue ordering, the items you've ordered are on their way.")

            failed_order_flag.clear()
            processing_flag.clear()

    async def handle_input(self):
        """ 
        Handle customer input using async events 
        """
        #clean_menu = ", ".join(re.findall(r"'(.*?)',\s*", self.agent.run('Can I see a Menu?')))
        #await self.text_to_speech("app/source/audio/audio_out/", f"Hello! I am EZ Serve, your artificially intelligent tableside assistant. The items on our menu are {clean_menu}")
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
                #if failed_order_flag.is_set():
                if False:
                    failed_record_flag.set()
                else:
                
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
                    
                if failed_record_flag.is_set():
                    print("Stopping recording!")
                    failed_record_flag.clear()

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

        self.agent = Agent(verbose=True)
