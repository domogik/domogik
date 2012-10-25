#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB emitter

import zmq
from random import choice
from time import sleep

MSG_VERSION = "0_1"

print("PUB-SUB emitter")
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.connect("tcp://localhost:5559")

categories = {
    'package' : ['installed', 'uninstalled'],
    'plugin' : ['enabled', 'disabled'],
}

while True:
    category = choice(categories.keys())
    action = choice(categories[category])
    message = "%s.%s.%s" %(category, action, MSG_VERSION)
    print("Sending message : %s" % message)
    socket.send(message)
    sleep(1)
    
    

