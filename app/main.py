"""Entrypoint for the app.
"""

from source import autoserve
import asyncio

server = autoserve.AutoServe(verbose=True)

asyncio.run(server.run())
