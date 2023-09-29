"""Transcriber module for transcribing wav files via Google api."""
import os
from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

WAVE_INPUT_FILENAME = "app/tmp/audio_file.wav"

def transcribe() -> object:
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint="us-central1-speech.googleapis.com",
        )
    )

    # Reads a file as bytes
    with open(WAVE_INPUT_FILENAME, "rb") as f:
        content = f.read()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="chirp",
    )

    project_id = os.getenv("SPEECH_PROJECT_ID")
    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/us-central1/recognizers/_",
        config=config,
        content=content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)

    if response.results[0] is not None:
        print("transcription: " + response.results[0].alternatives[0].transcript)
        return response.results[0].alternatives[0].transcript
    else:
        print("Empty response")
        return "empty response"
    