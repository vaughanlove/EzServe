
# EZ-Serve
Your AI server! Built for the Square + Google AI hackathon. Everything is intended to run off a raspberry pi.

<img src="ezserve.png" height="400">

## Features
- Place orders directly to Square using natural speech.
- Multi-language support for input/output speech.
- Error handling for ambiguous orders.

## Future Improvements
- switch text-to-speech to something more natural (https://coqui.ai/?)
- use whisper.cpp for local transcription. (faster, if possible)
- Further optimize the agent's prompt/template.
- Predictive Analytics & Demand Forecasting

## Challenges
We encountered many challenges throughout development. Listed below are many of the software and hardware challenges we encountered during the development process, these include:
* 
*
- initially was doing a bunch of regex and brute-forcing a list to find order items
  - upgraded to a vectordb.
- was having a bunch of issues minimizing the amount of text going through the LLM
  - changed to a custom agent framework to batch order calls.
- Was having issue when the program couldn't understand the user
  - added human-in-the-loop validation
- Mapping windows ports to unix ports.


## Architecture

### Current State - High Level Architecture
<img src="ezserve-current-state-diagram.png" height="400">

#### EZ-Serve Agent

### Ultimate Concept - High Level Architecture
<img src="ezserve-ultimate-state-diagram.png" height="400">


## Installation - Linux

1. initialize `.env` with env variables (example at .env.sample) 
2. ```pip install virtualenv```
3. `virtualenv venv`
4. `source venv/bin/activate`
5. `pip install -r requirements.txt`


## Installation - Windows

<b>audio is not supported on windows. you can still place orders to square via text in main.py</b>

1. initialize `.env` with env variables (example at .env.sample) 
2. ```git clone https://github.com/vaughanlove/EzServe```
3. Switch to `windows` branch
4. ```python3 -m venv venv```
5. ```.\venv\Scripts\activate```
6. ```python3 -m pip install -r .\requirements.txt```

## Run 

If you want to run the bot:                 `python3 app/main.py` 

(specifically python3)

If you want to work with the notebooks:  `pip install jupyterlab`, then  `jupyter lab`

## TODO

## In progress

- [x] Documentation + Demo
## Completed

- [x] Add human in the loop validation
- [x] Further customize agent template 
- [x] Create virtual terminal for visualizing results.
- [x] Documentation
- [x] Create custom langchain agent.
- [x] Make bot event loop robust.
- [x] Custom agent class.
- [x] Agent/Transcription error handling.
- [x] Add multi-language support.

## Formatting

Following Google's python style guide: [Google PyGuide](https://google.github.io/styleguide/pyguide.html)
(changed indent from 2 spaces to 4.)
