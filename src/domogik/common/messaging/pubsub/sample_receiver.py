#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB receiver

import zmq
import sys

def main(topic_filter):
    print("PUB-SUB receiver")
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5560")

    socket.setsockopt(zmq.SUBSCRIBE, topic_filter)

    while True:
        message_id = socket.recv()
        print("Message id : %s" % message_id)
        more = socket.getsockopt(zmq.RCVMORE)
        if more:
            message_content = socket.recv(zmq.RCVMORE)
            print("Message content : %s" % message_content)
        else:
            print("nothing more")

if __name__ == "__main__":
    topic_filter = ''
    if len(sys.argv) > 1:
        topic_filter = sys.argv[1]
    main(topic_filter)

