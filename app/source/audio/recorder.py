"""Recorder module for recording audio and stopped asyncronously"""

import pyaudio
import wave
import asyncio

stop_recording = asyncio.Event() 

class Recorder(object):
    WAVE_OUTPUT_FILENAME = "app/tmp/audio_file.wav"

    def __init__(self, trace=False, verbose=True) -> bool:
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024

        self.RECORDING = True

    
    async def start(self):
        task1 = asyncio.create_task(self.record())
        task2 = asyncio.create_task(self.handle_input())
        
        await task2
        await task1

    async def handle_input(self):
        print(f"""
              Currently {"recording" if self.RECORDING else "stopped"}. 
              Press r to record.
              Press s to stop recording.
              """)
        
        while True:
            user_input = await asyncio.to_thread(input, "Type something: ")  # Take user input asynchronously
            if user_input == 'r':
                if self.RECORDING:
                    print("Already recording!")
                else:
                    print("Starting the recording.")
                    self.RECORDING=True
                    stop_recording.clear()

            if user_input == 's':
                if not self.RECORDING:
                    print("Not recording!")
                else:
                    print("Stopping the recording.")
                    self.RECORDING = False
                    stop_recording.set()


    async def record(self):
        """opens audio stream and writes to wav file till stopped"""
        print("Opening stream")

        while True:

            p = pyaudio.PyAudio()

            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
            )
            frames = []

            while not stop_recording.is_set(): #mac keyboard work-around
                data = stream.read(self.CHUNK)
                frames.append(data)

                await asyncio.sleep(1 / 44100)  # This is hack but 1/ hz = seconds/sample and she works.

            # Close and terminate the stream
            stream.stop_stream()
            stream.close()
            SAMPLE_WIDTH = p.get_sample_size(self.FORMAT)
            p.terminate()

            # Save the audio data as a .wav file
            with wave.open(self.WAVE_OUTPUT_FILENAME, "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(SAMPLE_WIDTH)
                wf.setframerate(self.RATE)
                wf.writeframes(b"".join(frames))
                wf.close()

            print("recording saved!")

            while stop_recording.is_set():
                print("waiting for an update...")
                await asyncio.sleep(2.0)