#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB emitter

import zmq
from random import choice
from time import sleep

print("PUB-SUB emitter")
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.connect("tcp://localhost:5559")

countries = ['France', 'Germany', 'Italy', 'Spain']
events = ['Yellow card', 'Red card', 'Foul', 'Goal']

while True:
    topic = choice(countries)
    data = choice(events)
    message = "%s : %s" %(topic, data)
    print("Sending message : %s" % message)
    socket.send(message)
    sleep(1)
    
    

