from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

import pyaudio
import wave

import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
import numpy as np

import threading
import asyncio
import sys
import logging

logger = logging.getLogger(__name__)


async def text_to_speech(text: str):
        """
        Synthesizes speech from text and produces audio playback

        Args:
            text (string): text to synthesize speech from
        """
        
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
            
        event = asyncio.Event()
        current_frame = 0

        try:
            with sf.SoundFile("/home/dom/Desktop/autoserve/EzServe/app/source/audio/speaker_output.wav") as f:
                data = f.read(always_2d=True)
                
                current_frame = 0
                
                def callback(outdata, frames, time, status):
                    nonlocal current_frame
                    if status:
                        logger.debug(status)
                    chunksize = min(len(data) - current_frame, frames)
                    outdata[:chunksize] = data[current_frame:current_frame + chunksize]
                    if chunksize < frames:
                        outdata[chunksize:] = 0
                        raise sd.CallbackStop()
                    current_frame += chunksize
                        
                stream = sd.OutputStream(samplerate=25000, device=2, channels=data.shape[1], callback=callback, finished_callback=event.set)
                with stream:
                    await event.wait()  # Wait until playback is finished
        except Exception as e:
             logger.error(f"An error occured: {e}")
