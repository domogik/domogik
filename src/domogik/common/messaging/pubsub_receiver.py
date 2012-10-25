#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB receiver

import zmq

print("PUB-SUB receiver")
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5560")

topicfilter = "Italy"
socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

while True:
    message = socket.recv()
    print(message)

