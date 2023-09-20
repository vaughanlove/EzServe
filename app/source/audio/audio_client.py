"""Records and Transcribes audio."""

import os
from recorder import Recorder
from transcriber import Transcriber
from translator import Translator

class AudioClient(object):
    """Used by autoserve for handling audio input and transcription."""
    def __init__(self, trace=False, verbose=True) -> bool:
        #ensure google credentials are set (may have to use google project number for ID)
        assert os.getenv("GOOGLE_PROJECT_ID") is not None, "MISSING GOOGLE_PROJECT_ID"
        assert os.getenv("API_KEY") is not None, "MISSING API_KEY"

    def listen(self) -> object:
        """Record audio until user inputted stop.
        
        Returns (str):  Transcript 
        """
        # record audio to .wav until user inputted aync stop
        input("Press enter to start recording")
        recorder = Recorder()
        audio = recorder.record()
        
        if(audio):
            # transcribe .wav audio to text
            print("Transcribing...")
            transcriber = Transcriber()
            transcript = transcriber.transcribe()

            print("TRANSLATING...")
            translator = Translator()
            result = translator.translate(transcript)
            print("Final: " +result)
            return result
        
        return "empty response"

#SAMPLE USAGE
# def main():
#     client = AudioClient()
#     client.listen()

# if __name__ == "__main__":
#     main()