import os 
from enum import Enum
import threading

from langchain.agents import AgentType, initialize_agent
from langchain.llms import vertexai

from google.cloud import aiplatform
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

from dotenv import load_dotenv
import pyaudio
import wave

# Event object to control the loop and thread termination
stop_event = threading.Event()

def check_user_input():
    while not stop_event.is_set():
        user_input = input("Do you want to stop the recording? (y/n): ")
        if user_input.lower() == 'y':
            stop_event.set()
            print("Loop will be stopped.")
            break

# refactor into own subdir?
from .tools import OrderTool, GetDetailedMenuTool, FindItemIdTool, MakeOrderCheckoutTool, GetOrderTool

class State(Enum):
    RECORDING = 1
    PROCESSING = 2
    WAITING = 3

class AutoServe():
    state = State.WAITING
    
    history = []
    transcribed_string = None
    WAVE_OUTPUT_FILENAME = "app/tmp/audio_file.wav"

    
    agent = None
    llm = None
    tools = [GetDetailedMenuTool(), FindItemIdTool(), OrderTool(), MakeOrderCheckoutTool(), GetOrderTool()]
    
    def __init__(self, trace=False, verbose=True) -> bool:
        self.__loadEnvironmentVariables(trace)
        self.__setupGCloud()

        self.llm = vertexai.VertexAI(temperature=0)
        assert self.llm != None, "LLM NOT INSTANTIATED"

        assert len(self.tools) > 0, "NEED AT LEAST ONE TOOL"

        self.agent = initialize_agent (    
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose
        )

    def start(self) -> None:
        self.state = State.RECORDING

        p = pyaudio.PyAudio()

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = 5

        print("Opening stream")

        stream = p.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)
        
        print("Recording...")

        print("starting the user input thread")
        # Start the user input thread
        input_thread = threading.Thread(target=check_user_input)
        input_thread.start()

        frames = []

        # Record audio
        # TODO: make this stop when user inputs 'stop' - instead of just after 5 seconds. '

        while True:
            if stop_event.is_set():
                print("Loop has been stopped.")
                break
            data = stream.read(CHUNK)
            frames.append(data)


        # Close and terminate the stream
        print("Finished recording.")
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Signal the user input thread to terminate
        stop_event.set()

# Wait for the user input thread to terminate
        input_thread.join()
        # Save the audio data as a .wav file
        with wave.open(self.WAVE_OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        return self.process()

    def process(self):
        self.state = State.PROCESSING
        print("Start processing")
        client = SpeechClient()

        # Reads a file as bytes
        with open(self.WAVE_OUTPUT_FILENAME, "rb") as f:
            content = f.read()

        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="short",
        )

        PROJECT_ID = os.getenv("SPEECH_PROJECT_ID")
        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
            config=config,
            content=content,
        )

        # Transcribes the audio into text
        response = client.recognize(request=request)

        print("TRANSCRIPTION: " + response.results[0].alternatives[0].transcript)
        #for result in response.results:
        #    print(f"Transcript: {result.alternatives[0].transcript}")

        agent_response =  self.agent.run(response.results[0].alternatives[0].transcript) 
        self.state = State.WAITING
        return agent_response
    
    def stop(self) -> None:
        self.state = State.PROCESSING
        # do the speech=> text and load text into member variable
        

    def getState(self) -> State:
        return self.state
    

        
    def __loadEnvironmentVariables(self, trace: bool) -> None:
        # load environment variables from .env file
        load_dotenv()

        assert os.getenv("GOOGLE_PROJECT_ID") != None, ".ENV MISSING GOOGLE_PROJECT_ID"
        assert os.getenv("LOCATION") != None, ".ENV MISSING LOCATION"
        assert os.getenv("API_KEY") != None, ".ENV MISSING API_KEY"

        # trace langchain execution
        os.environ["LANGCHAIN_TRACING"] = 'false' if not trace else 'true'

        # square device id presets. More info at https://developer.squareup.com/docs/devtools/sandbox/testing
        DEVICE_ID_CHECKOUT_SUCCESS="9fa747a2-25ff-48ee-b078-04381f7c828f"
        DEVICE_ID_CHECKOUT_SUCCESS_TIP="22cd266c-6246-4c06-9983-67f0c26346b0"
        DEVICE_ID_CHECKOUT_SUCCESS_GC="4mp4e78c-88ed-4d55-a269-8008dfe14e9"
        DEVICE_ID_CHECKOUT_FAILURE_BUYER_CANCEL="841100b9-ee60-4537-9bcf-e30b2ba5e215"

        # set what device ID to use
        os.environ["DEVICE"] = DEVICE_ID_CHECKOUT_SUCCESS_TIP
    
    def __setupGCloud(self) -> None:
        GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID") # ie, confident-jackle-123456
        aiplatform.init(project=GOOGLE_PROJECT_ID, location="us-central1")

    def __loadTools(self) -> None:
        pass

# authenticate 
