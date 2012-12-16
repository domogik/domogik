#!/usr/bin/python
# -*- coding: utf-8 -*-

# Utility class for publish / subscribe pattern

import json
import zmq
from time import sleep, time
from domogik.common import logger

MSG_VERSION = "0_1"
PORT_PUB = "tcp://localhost:5559"
PORT_SUB = "tcp://localhost:5560"

class MessagingEvent:
    def __init__(self):
        self.context = zmq.Context()

class MessagingEventPub(MessagingEvent):
    def __init__(self):
        MessagingEvent.__init__(self)
        self.log = logger.Logger('mq_event_pub').get_logger()
        self.s_send = self.context.socket(zmq.PUB)
        self.s_send.connect(PORT_PUB)
    
    def send_event(self, category, action, content):
        """Send an event in JSON format with two keys : 'id' and 'content'

        @param category : category of the message
        @param action : action corresponding to the message
        @param content : content of the message : must be in JSON format

        """
        msg_id = "%s.%s.%s.%s" %(category, action, str(time()).replace('.','_'), MSG_VERSION)
        msg = json.dumps({'id': msg_id, 'content': content})
        self.s_send.send(msg)
        self.log.debug("Message sent : %s" % msg)

class MessagingEventSub(MessagingEvent):
    def __init__(self, category_filter=None, action_filter=None):
        MessagingEvent.__init__(self)
        self.log = logger.Logger('mq_event_sub').get_logger()
        self.s_recv = self.context.socket(zmq.SUB)
        self.s_recv.connect(PORT_SUB)
        topic_filter = ''
        if category_filter is not None and len(str(category_filter)) > 0:
            topic_filter = category_filter
            if action_filter is not None and len(str(action_filter)) > 0:
                topic_filter += "." + action_filter
        print("Topic filter : %s" % topic_filter)
        self.s_recv.setsockopt(zmq.SUBSCRIBE, topic_filter)
    
    def wait_for_event(self):
        """Receive an event

        @return : event message in JSON format with two keys : 'id' and 'content'

        """
        event = self.s_recv.recv()
        self.log.debug("Message received %s" %event)
        return event
