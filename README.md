
# Auto Serve

## setup

### Server
Using docker:

1. `git clone auto-serve`
2. Build: `docker compose build`
3. Run: `docker compose up`

### Notebooks
#### conda

1. `conda env create -f environment.yaml`
2. `conda activate autoserve`
3. `jupyter lab`

#### pip

1. (recommended) create a virtual environment.
2. `pip install -r requirements.txt`
3. `jupyter lab` 

![DFD-High-Level Architecture drawio](https://github.com/vaughanlove/square-serve/assets/57467835/21e105cb-2171-49de-868d-1bc002ac9174)
