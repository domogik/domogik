#!/usr/bin/python
# -*- coding: utf-8 -*-

# Utility class to send / receive events

import zmq
from time import sleep

MSG_VERSION = "0_1"
PORT_PUB = "tcp://localhost:5559"
PORT_SUB = "tcp://localhost:5560"

class MessagingEvent:
    def __init__(self):
        self.context = zmq.Context()

class MessagingEventPub(MessagingEvent):
    def __init__(self):
        MessagingEvent.__init__(self)
        self.s_send = self.context.socket(zmq.PUB)
        self.s_send.connect(PORT_PUB)
    
    def send_message(self, category, action, content):
        msg_id = "%s.%s.%s" %(category, action, MSG_VERSION)
        self.s_send.send(content)
        self.s_send.send(msg_id, zmq.SNDMORE)
        print("Message sent : %s : %s" % (msg_id, content))
        sleep(1)

class MessagingEventSub(MessagingEvent):
    def __init__(self, category_filter=None, action_filter=None):
        MessagingEvent.__init__(self)
        self.s_recv = self.context.socket(zmq.SUB)
        self.s_recv.connect(PORT_SUB)
        topic_filter = ''
        if category_filter is not None and len(str(category_filter)) > 0:
            topic_filter = category_filter
            if action_filter is not None and len(str(action_filter)) > 0:
                topic_filter += "." + action_filter
        print("Topic filter : %s" % topic_filter)
        self.s_recv.setsockopt(zmq.SUBSCRIBE, topic_filter)
    
    def wait_for_message(self):
        message_id = self.s_recv.recv()
        print("Message id : %s" % message_id)
        more = self.s_recv.getsockopt(zmq.RCVMORE)
        if more:
            message_content = self.s_recv.recv(zmq.RCVMORE)
            #print("Message content : %s" % message_content)
            return message_content
        else:
            print("nothing more")
        
