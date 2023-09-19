"""Records and Transcribes audio."""

import os
from recorder import Recorder
from transcriber import Transcriber

class AudioClient(object):
    """Used by autoserve for handling audio input and transcription."""
    def __init__(self, trace=False, verbose=True) -> bool:
        #ensure google credentials are set (may have to use google project number for ID)
        assert os.getenv("GOOGLE_PROJECT_ID") is not None, "MISSING GOOGLE_PROJECT_ID"
        assert os.getenv("API_KEY") is not None, "API_KEY"

    def listen(self) -> object:
        """Record audio until user inputted stop.
        
        Returns (str):  Transcript 
        """
        # record audio until user inputted aync stop
        input("Press enter to start recording")
        recorder = Recorder()
        audio = recorder.record()

        print("Transcribing...")
        transcriber = Transcriber()
        transcript = transcriber.transcribe()

        print("Final transcription: " +transcript)

        return transcript

def main():
    client = AudioClient()
    client.listen()

if __name__ == "__main__":
    main()