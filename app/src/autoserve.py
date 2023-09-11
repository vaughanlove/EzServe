import os 

from langchain.agents import AgentType, initialize_agent
from google.cloud import aiplatform
from langchain.llms import vertexai
from dotenv import load_dotenv

# refactor into own subdir?
from .tools import OrderTool, GetDetailedMenuTool, FindItemIdTool, MakeOrderCheckoutTool, GetOrderTool

class AutoServe():
    agent = None
    llm = None
    tools = [GetDetailedMenuTool(), FindItemIdTool(), OrderTool(), MakeOrderCheckoutTool(), GetOrderTool()]
    
    def __init__(self, trace=False) -> bool:
        self.__loadEnvironmentVariables(trace)
        self.__setupGCloud()

        self.llm = vertexai.VertexAI(temperature=0)
        assert self.llm != None, "LLM NOT INSTANTIATED"

        assert len(self.tools) > 0, "NEED AT LEAST ONE TOOL"

        self.agent = initialize_agent (    
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

    def start(self) -> None:
        pass
        
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
