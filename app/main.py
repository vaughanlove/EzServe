"""
Entrypoint for the app.
"""

from source import autoserve
import asyncio

# enable verbose to see agent thoughts.
server = autoserve.AutoServe(verbose=True)

#server.agent.run("I would like a small milkshake")
asyncio.run(server.run())
