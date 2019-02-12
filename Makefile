.PHONY: clean test lint

TEST_PATH=./

help:
	@echo "    train-nlu"
	@echo "        Train the natural language understanding using Rasa NLU."
	@echo "    train-core"
	@echo "        Train a dialogue model using Rasa core."
	@echo "    run-action"
	@echo "        Run the action server."
	@echo "    run-cmdline"
	@echo "        Starts the bot on the command line"
	@echo "    run-monitor"
	@echo "        Run the monitor system."
	@echo "    run-tele"
	@echo "        Run the rasa-core with telegram intergration."
	@echo "    visualize"
	@echo "        Saves the story graphs into a file"
	@echo "    evaluate-core"
	@echo "        Evaluate core"
	@echo "    clean"
	@echo "        Delete models."

train-nlu:
	python3 -m rasa_nlu.train -c nlu_config.yml --data data/nlu -o models --fixed_model_name current --project nlu --verbose

train-core:
	python3 -m rasa_core.train -d domain.yml -s data/core -o models/dialogue -c policy.yml

train-all:
	make train-nlu && make train-core

run-action:
	python3 -m rasa_core_sdk.endpoint --actions main.actions

run-cmdline:
	python3 -m rasa_core.run -d models/dialogue -u models/nlu/current --debug --endpoints endpoints.yml

run-monitor:
	python3 monitor/monitor.py

run-tele:
	python3 -m rasa_core.run -d models/dialogue -u models/nlu/current --port 6000 --endpoints endpoints.yml --credentials ../credentials.yml

visualize:
	python3 -m rasa_core.visualize -s data/core/ -d domain.yml -o story_graph.png

evaluate-core:
	python3 -m rasa_core.evaluate --core models/dialogue -s data/core/ --fail_on_prediction_errors

clean:
	rm -rf models/*
