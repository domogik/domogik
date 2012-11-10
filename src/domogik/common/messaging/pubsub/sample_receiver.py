#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB receiver

import sys
from messaging_event import MessagingEventSub

def main(category_filter, action_filter):
    print("PUB-SUB receiver")
    '''
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5560")

    socket.setsockopt(zmq.SUBSCRIBE, topic_filter)
    '''

    sub_event = MessagingEventSub(category_filter, action_filter)

    while True:
        msg = sub_event.wait_for_event()
        print(msg)
        '''
        print("Message id : %s" % message_id)
        more = socket.getsockopt(zmq.RCVMORE)
        if more:
            message_content = socket.recv(zmq.RCVMORE)
            print("Message content : %s" % message_content)
        else:
            print("nothing more")
        '''

if __name__ == "__main__":
    category_filter = None
    action_filter = None
    if len(sys.argv) > 1:
        category_filter = sys.argv[1]
    if len(sys.argv) > 2:
        action_filter = sys.argv[2]
    main(category_filter, action_filter)

