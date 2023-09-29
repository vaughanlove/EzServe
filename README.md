
# Auto Serve

To install see [Installation](#installation)

If you want to run the bot:                 `python app/main.py` 

If you want to work with the notebooks:  `pip install jupyterlab`, then  `jupyter lab`

## TODO

- [x] Make bot event loop robust.
- [x] Custom agent class.
- [ ] Agent/Transcription error handling.
- [ ] Add multi-language support.

## In progress

- [ ] Create virtual terminal for visualizing results.
- [ ] Documentation
- [ ] Create custom langchain agent.

## Installation

### pip

1. ```pip install virtualenv```
2. `virtualenv venv`
3. Windows: `venv/Scripts/activate`, Linux: `source venv/bin/activate`
4. `pip install -r requirements.txt`

## Formatting

Following Google's python style guide: [Google PyGuide](https://google.github.io/styleguide/pyguide.html)
(changed indent from 2 spaces to 4.)

![DFD-High-Level Architecture drawio](https://github.com/vaughanlove/square-serve/assets/57467835/21e105cb-2171-49de-868d-1bc002ac9174)
