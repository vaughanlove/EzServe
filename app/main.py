from src import autoserve 

import time
from time import sleep

client = autoserve.AutoServe(verbose=False)
#test = client.agent.run("Could I order a small coffee please?")

# need to mess with concurrency?
# here is where the chirp model records/transcribes/returns string


# take user input to start recording
def HandleInput(state: autoserve.State):
    if state.name == 'WAITING':
        value = input(
            f"""
            CURRENT: {client.getState().name}\n
            inputs: \n
            `r` - RECORD
            `s` - STOP 
            """
        )
        if value == 'r':
            value = client.start()
            print(value)
        elif value == 's':
            print("Client is already stopped.")


RUNNING = True
while (RUNNING):
    HandleInput(client.getState())

    sleep(1)



