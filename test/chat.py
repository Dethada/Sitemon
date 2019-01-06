#!/usr/bin/env python3
from rasa_core.agent import Agent
from rasa_core.interpreter import RasaNLUInterpreter
import time

interpreter = RasaNLUInterpreter('models/nlu/current')
welcome = "Hi! you can chat in this window. Type 'stop' to end the conversation."
agent = Agent.load('models/dialogue', interpreter=interpreter, action_endpoint='http://192.168.14.138:5055/webhook')

print(welcome)
while True:
    time.sleep(0.3)
    a = input('You: ')
    if a == 'stop':
        break
    responses = agent.handle_message(a)
    agent.execute_action(a)
    for r in responses:
        print('Bot: {}'.format(r))