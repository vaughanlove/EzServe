"""
Transcriber module for transcribing wav files via Google api.
"""

from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

import os
import logging

logger = logging.getLogger(__name__)
def transcribe(path: str) -> object:
    """
    Reads audio file and transcribes to text.

    Args:
        path (string): path to .wav audio file to transcribe to text
    Returns: 
        Transcribed audio to text string
    """
    # Instantiate Gcloud speech client
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint="us-central1-speech.googleapis.com",
        )
    )

    # Reads a file as bytes
    with open(path, "rb") as f:
        content = f.read()
        f.close()

    # Gcloud recognition configuration
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="chirp",
    )

    # Generate speech recognizer request
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/us-central1/recognizers/_",
        config=config,
        content=content,
    )
    
    # Transcribes the audio into text
    response = client.recognize(request=request)
    
    # return result transcribed results
    if len(response.results) != 0:
        logger.info(f"transcription finished: {response.results[0].alternatives[0].transcript}.")
        return response.results[0].alternatives[0].transcript
    else:
        logger.info("the transcription was empty.")
        return "empty response"
