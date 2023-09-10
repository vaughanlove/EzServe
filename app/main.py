import os
import json

from pprint import pprint

from langchain import LLMChain, PromptTemplate
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor, AgentType, initialize_agent
from langchain.llms import vertexai
from langchain.tools.base import BaseTool
from langchain.callbacks.manager import (AsyncCallbackManagerForToolRun, CallbackManagerForToolRun)


from vertexai.preview.language_models import TextGenerationModel
from google.cloud import aiplatform

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Type