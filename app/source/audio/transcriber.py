"""Transcriber module for transcribing wav files via Google api."""
import os
import wave
from google.cloud import aiplatform
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

class Transcriber(object):
    WAVE_INPUT_FILENAME = "tmp/audio_file.wav"

    def __init__(self, trace=False, verbose=True) -> bool:
        google_project_id = os.getenv(
            "GOOGLE_PROJECT_ID"
        )  # ie, confident-jackle-123456
        aiplatform.init(project=google_project_id, location="us-central1")

    def transcribe(self) -> object:
        client = SpeechClient()

        # Reads a file as bytes
        with open(self.WAVE_INPUT_FILENAME, "rb") as f:
            content = f.read()

        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="short",
        )

        project_id = os.getenv("SPEECH_PROJECT_ID")
        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{project_id}/locations/global/recognizers/_",
            config=config,
            content=content,
        )

        # Transcribes the audio into text
        response = client.recognize(request=request)

        if response.results[0] != None:
            print("TRANSCRIPTION: " + response.results[0].alternatives[0].transcript)
            return response.results[0].alternatives[0].transcript
        else:
            print("Empty response")
            return "empty response"