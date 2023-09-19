"""Entrypoint for the app.
"""

from source import autoserve
import asyncio

#verbose here is referring to the langchain AgentExecutor logic.
server = autoserve.AutoServe(verbose=False)

asyncio.run(server.run())
