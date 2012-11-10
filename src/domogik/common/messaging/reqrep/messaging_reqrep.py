#!/usr/bin/python
# -*- coding: utf-8 -*-

# Utility class for request / reply pattern

import zmq
from time import sleep

MSG_VERSION = "0_1"
PORT_REQ = "tcp://localhost:6559"
PORT_REP = "tcp://localhost:6560"

class MessagingReqRep:
    def __init__(self):
        self.context = zmq.Context()

class MessagingReq(MessagingReqRep):
    def __init__(self):
        MessagingReqRep.__init__(self)
        self.s_req = self.context.socket(zmq.REQ)
        self.s_req.connect(PORT_REQ)
    
    def send_request(self, category, action, request_content):
        request_id = "%s.%s.%s" %(category, action, MSG_VERSION)
        request = "%s : %s" % (request_id, request_content)
        self.s_req.send(request)
        print("Request sent : %s, waiting for reply..." % request)
        
        reply = self.s_req.recv()

        return reply

class MessagingRep(MessagingReqRep):
    def __init__(self):
        MessagingReqRep.__init__(self)
        self.s_rep = self.context.socket(zmq.REP)
        self.s_rep.connect(PORT_REP)
    
    def wait_for_request(self):
        request = self.s_rep.recv()
        return request
    
    def send_reply(self, reply_content):
        reply_id = "reply"
        reply = "%s : %s" % (reply_id, reply_content)
        self.s_rep.send(reply)
        print("Reply sent : %s" % reply)
        
