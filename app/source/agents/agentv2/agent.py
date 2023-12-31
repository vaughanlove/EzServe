""" v2 of the agent class. 
This approach significantly lowered the # of calls to the LLM,
and increased the amount of information we can convey to the business through `note`.

Using weaviate for the vector database.
"""


from source.agents.agentv2.template import template
from source.agents.agentv2.prompt import CustomPromptTemplate
from source.agents.agentv2.output import CustomOutputParser
from source.agents.agentv2.ordertools import OrderTool, DescriptionTool, MenuTool, NoOrderTool, GetUserOrderTool, OrderCheckoutTool

from langchain.llms import vertexai
from langchain.chains import LLMChain
from langchain.agents import LLMSingleActionAgent, AgentExecutor

import logging

logger = logging.getLogger(__name__)

class Agent():
    """Agent class to provide the run() entrypoint to query the llm. 
    """
    def run(self, user_input: str) -> str:
        logger.info(f"querying the agent with: {user_input}")
        return self.agent_executor.run(user_input)

    def __init__(self, verbose):
        """initializes the agent's tools, prompt template, llm, output_parser."""
        # add tools you want the agent to use.
        self.tools = [
            OrderTool,
            NoOrderTool,
            DescriptionTool,
            OrderCheckoutTool
        ]
        self.tool_names = [x.name for x in self.tools]

        # initialize the prompt.
        self.prompt = CustomPromptTemplate(
            template=template,
            tools=self.tools,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            input_variables=["input", "intermediate_steps"]
        )

        # define LLM parameters
        self.output_parser = CustomOutputParser()
        self.llm = vertexai.VertexAI(tempurature=0)
        self.llm_chain = LLMChain(llm=self.llm, prompt=self.prompt)

        # configure LLM agent
        self.agent = LLMSingleActionAgent(
            llm_chain=self.llm_chain,
            output_parser=self.output_parser,
            stop=["\nObservation:"],
            allowed_tools=self.tool_names
        )

        # configure agent execution
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose
        )
        
