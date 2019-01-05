.PHONY: clean test lint

TEST_PATH=./

help:
	@echo "    train-nlu"
	@echo "        Train the natural language understanding using Rasa NLU."
	@echo "    train-core"
	@echo "        Train a dialogue model using Rasa core."
	@echo "    run-cmdline"
	@echo "        Starts the bot on the command line"
	@echo "    visualize"
	@echo "        Saves the story graphs into a file"

run-actions:
	python3 -m rasa_core_sdk.endpoint --actions main.actions

train-nlu:
	python3 -m rasa_nlu.train -c nlu_config.yml --data data/nlu -o models --fixed_model_name current --project nlu --verbose

train-core:
	python3 -m rasa_core.train -d domain.yml -s data/core -o models/dialogue #-c policy.yml

train-all:
	make train-nlu && make train-core

run-cmdline:
	make run-actions &
	python3 -m rasa_core.run -d models/dialogue -u models/nlu/current --debug --endpoints endpoints.yml

visualize:
	python3 -m rasa_core.visualize -s data/core/ -d domain.yml -o story_graph.png

evaluate-core:
	python -m rasa_core.evaluate --core models/dialogue -s data/core/ --fail_on_prediction_errors
