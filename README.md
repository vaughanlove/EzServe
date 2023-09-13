
# Auto Serve

## Installation

#### conda

1. `conda env create -f environment.yaml`
2. `conda activate autoserve`


#### pip

1. Create a virtual env: `python -m venv venv`
2. `venv/Scripts/activate`
3. `pip install -r requirements.txt`

If you want to work with the notebooks:     `jupyter lab`
If you want to run the bot:                 `python app/main.py` 

#### docker

** not using docker during development - using windows devices inside a linux container is very jank.**

1. `git clone auto-serve`
2. Build: `docker compose build`
3. Run: `docker compose up`


## TODO
1. Make bot event loop robust
2. Custom agent class
3. Create virtual terminal for visualizing results.
4. Testing
5. Agent/Transcription error handling
6. Documentation

## Formatting

Following Google's python style guide: https://google.github.io/styleguide/pyguide.html 
- changed indent from 2 spaces to 4.


![DFD-High-Level Architecture drawio](https://github.com/vaughanlove/square-serve/assets/57467835/21e105cb-2171-49de-868d-1bc002ac9174)
