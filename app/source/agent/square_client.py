from source.agent.tools import (
    OrderTool,
    GetDetailedMenuTool,
    FindItemIdTool,
    MakeOrderCheckoutTool,
    GetOrderTool,
)

from langchain.agents import AgentType, initialize_agent
from langchain.llms import vertexai

class SquareClient():
    """
    """
    def __init__(self, trace=False, verbose=True) -> bool:
        self.llm = vertexai.VertexAI(temperature=0)

        self.tools = [
            GetDetailedMenuTool(),
            FindItemIdTool(),
            OrderTool(),
            MakeOrderCheckoutTool(),
            GetOrderTool(),
        ]

        assert self.llm is not None, "LLM NOT INSTANTIATED"
        assert len(self.tools) > 0, "NEED AT LEAST ONE TOOL"

        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose,
        )

    def run(self, prompt):
        res = self.agent.run(prompt)
        return res