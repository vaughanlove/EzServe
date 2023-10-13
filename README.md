
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

## Challenges we faced

## Architecture
## Installation
### pip

1. ```pip install virtualenv```
2. `virtualenv venv`
3. Windows: `venv/Scripts/activate`, Linux: `source venv/bin/activate`
4. `pip install -r requirements.txt`

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