"""Recorder module for recording audio and stopped asyncronously"""

import pyaudio
import wave
import asyncio

from source.audio.transcriber import Transcriber
from source.agent.square_client import SquareClient

class Recorder(object):
    WAVE_OUTPUT_FILENAME = "app/tmp/audio_file.wav"

    def __init__(self, trace=False, verbose=True) -> bool:
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024

        self.recording = True

        self.t = Transcriber()
        self.agent = SquareClient(trace=trace, verbose=verbose)

    async def record(self, stop_recording):
        """opens audio stream and writes to wav file till stopped"""
        #print("Record task running")

        while True:
            
            while stop_recording.is_set():
                await asyncio.sleep(0.2)

            p = pyaudio.PyAudio()

            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )
            frames = []

            while not stop_recording.is_set(): #mac keyboard work-around
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

            #print("recording saved!")

            # do the transcription
            transcript = self.t.transcribe()

            agent_response = self.agent.run(transcript)

            #play agent_response?
            print("AGENT: " + agent_response)

