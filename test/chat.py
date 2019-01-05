#!/usr/bin/env python3
from rasa_core.agent import Agent
from rasa_core.interpreter import RasaNLUInterpreter
import time

interpreter = RasaNLUInterpreter('models/nlu/current')
messages = ["Hi! you can chat in this window. Type 'stop' to end the conversation."]
agent = Agent.load('models/dialogue', interpreter=interpreter)

print(messages[0])
while True:
    # print(messages[-1])
    time.sleep(0.3)
    a = input('You: ')
    messages.append(a)
    if a == 'stop':
        break
    responses = agent.handle_message(a)
    for r in responses:
        print('Bot: {}'.format(r))