"""
Transcriber module for transcribing wav files via Google api.
"""
import os
from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


def transcribe() -> object:
    """
    Reads audio file and transcribes to text.
    """
    # Instantiate Gcloud speech client
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint="us-central1-speech.googleapis.com",
        )
    )
    # Search audio_input folder for .wav files.
    # *** Assumes there is one has tempfile is set to delete customer input after each sequential order. ***
    WAVE_INPUT_FOLDER = os.getcwd() + "/app/source/audio/audio_in"
    ALL_WAV = os.listdir(WAVE_INPUT_FOLDER)
    WAV_FILES = [file for file in ALL_WAV if file.endswith(".wav")]
    WAVE_INPUT_FILENAME = os.path.join(WAVE_INPUT_FOLDER, WAV_FILES[0])

    # Reads a file as bytes
    with open(WAVE_INPUT_FILENAME, "rb") as f:
        content = f.read()
        f.close()

    # Gcloud recognition configuration
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="chirp",
    )

    project_id = os.getenv("GOOGLE_PROJECT_ID")
    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/us-central1/recognizers/_",
        config=config,
        content=content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)
    
    # return result transcribed results
    if response.results[0] is not None:
        print(f"EzServe - Received Transcription: {response.results[0].alternatives[0].transcript}.")
        return response.results[0].alternatives[0].transcript
    else:
        print("EzServe - Empty response.")
        return "empty response"
