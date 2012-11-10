#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB emitter

import zmq
import json
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
    message_id = "%s.%s.%s" %(category, action, MSG_VERSION)
    message_content = json.dumps({"content" : "This is the message content"})
    #message = json.dumps({message_id : message_content})
    print("Sending message : %s : %s" % (message_id, message_content))
    socket.send(message_content)
    socket.send(message_id, zmq.SNDMORE)
    sleep(1)
    
    

