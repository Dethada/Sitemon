# Sitemon Bot

## Requirements
- Python >= 3.6
- [Pipenv](https://pipenv.readthedocs.io/en/latest/)

## Setup
```bash
# install packages
pipenv install
# drop into virtualenv
pipenv shell
# train model
make train-all
# run the action server in vm/docker and set the ip in endpoints.yml
python3 -m rasa_core_sdk.endpoint --actions main.actions
# test model
make run-cmdline
```