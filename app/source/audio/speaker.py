from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

import pyaudio
import wave

import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
import threading
import numpy as np
import asyncio
import sys

import logging
log = logging.getLogger("autoserve")
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def text_to_speech(text: str):
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
    
    output_file = "app/source/audio/speaker_output.wav"
    with wave.open(output_file, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(25000)
        wf.writeframes(response.audio_content)
    print(f"Response : {response.audio_content}")
    await play_wav_bytes()

current_frame = 0
        
async def play_wav_bytes():
    event = asyncio.Event()
    try:
        with sf.SoundFile("/home/dom/Desktop/autoserve/EzServe/app/source/audio/speaker_ouput.wav") as f:
            data, fs = f.read(always_2d=True)
            
            def callback(outdata, frames, time, status):
                global current_frame
                if status:
                    print(status)
                chunksize = min(len(data) - current_frame, frames)
                outdata[:chunksize] = data[current_frame:current_frame + chunksize]
                if chunksize < frames:
                    outdata[chunksize:] = 0
                    raise sd.CallbackStop()
                current_frame += chunksize
                    

            stream = sd.OutputStream(samplerate=fs, device=2, channels=data.shape[1], callback=callback, finished_callback=event.set)
            with stream:
                event.wait()  # Wait until playback is finished
    except Exception as e:
         print(f"An error occured: {e}")
