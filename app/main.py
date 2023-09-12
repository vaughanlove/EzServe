"""Entrypoint for the app. Initates the client object and handles user inputs.
"""
from src import autoserve
from time import sleep

client = autoserve.AutoServe(verbose=False)


# take user input to start recording
def HandleInput(state: autoserve.State):
    """
    Poll and handle user input.

    :param state: The current state of the system.
    :type state: autoserve.State
    :return: None
    """
    if state.name == "WAITING":
        value = input(
            f"""
            CURRENT: {client.get_state().name}\n
            inputs: \n
            `r` - RECORD
            `s` - STOP 
            """
        )
        if value == "r":
            value = client.start()
            print(value)
        elif value == "s":
            print("Client is already stopped.")


RUNNING = True
while RUNNING:
    HandleInput(client.get_state())

    sleep(1)
