from template import template
from prompt import CustomPromptTemplate
from output import CustomOutputParser
from langchain.llms import vertexai
from langchain.chains import LLMChain
from langchain.agents import LLMSingleActionAgent, AgentExecutor

from ordertools import OrderTool

from google.cloud import aiplatform

from dotenv import load_dotenv

import os

load_dotenv()
aiplatform.init(project=os.getenv("GOOGLE_PROJECT_ID"), location="us-central1")

tools = [OrderTool()]
tool_names = [x.name for x in tools]

prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    # This includes the `intermediate_steps` variable because that is needed
    input_variables=["input", "intermediate_steps"]
)

output_parser = CustomOutputParser()

llm = vertexai.VertexAI(tempurature=0)
llm_chain = LLMChain(llm=llm, prompt=prompt)


agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=output_parser,
    stop=["\nObservation:"],
    allowed_tools=tool_names
)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True
    )

agent_executor.run("Hello, what tools do you have access to?")