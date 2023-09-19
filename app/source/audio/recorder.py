"""Recorder module for recording audio and stopped asyncronously"""

import pyaudio
import wave
import keyboard

class Recorder(object):
    WAVE_OUTPUT_FILENAME = "tmp/audio_file.wav"

    def __init__(self, trace=False, verbose=True) -> bool:
        self.p = pyaudio.PyAudio()

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024
        self.RECORD_SECONDS = 10

    def record(self):
        """opens audio stream and writes to wav file till stopped"""
        print("Opening stream")

        stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )
        frames = []

        
        #for _ in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)): #record for RECORD_SECONDS
        # Record audio
        #keyboard.is_pressed("r"): #doesnt work on mac, better to use than input()
        print("Recording... (Press r to stop)")
        while not input() == "r": #mac keyboard work-around
            data = stream.read(self.CHUNK)
            frames.append(data)

        # Close and terminate the stream
        stream.stop_stream()
        stream.close()
        self.p.terminate()

        # Save the audio data as a .wav file
        with wave.open(self.WAVE_OUTPUT_FILENAME, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b"".join(frames))

        return