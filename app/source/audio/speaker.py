from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()
import pyaudio
import wave
from pydub import AudioSegment

def text_to_speech(text: str):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
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

    play_wav_bytes(response.audio_content)

def play_wav_bytes(wav_bytes):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a PyAudio stream
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=25000,
                    output=True)

    # Play the audio data
    stream.write(wav_bytes)

    # Close the stream when finished
    stream.stop_stream()
    stream.close()
