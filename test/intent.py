#!/usr/bin/env python3
from rasa_nlu.model import Metadata, Interpreter
import json


def pprint(o):
 # small helper to make dict dumps a bit prettier
    print(json.dumps(o, indent=2))


interpreter = Interpreter.load('./models/current/nlu')
# pprint(interpreter.parse(u"Hello"))

while True:
    a = input('You: ')
    if a == 'stop':
        break
    pprint(interpreter.parse(a))
