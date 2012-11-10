#!/usr/bin/python
# -*- coding: utf-8 -*-

# Utility class for request / reply pattern

import zmq
import time
import json

MSG_VERSION = "0_1"
PORT_REQ = "tcp://localhost:6559"
PORT_REP = "tcp://localhost:6560"

REQ_PREFIX = "req"
REP_PREFIX = "rep"

class MessagingReqRep:
    def __init__(self):
        self.context = zmq.Context()

class MessagingReq(MessagingReqRep):
    def __init__(self):
        MessagingReqRep.__init__(self)
        self.s_req = self.context.socket(zmq.REQ)
        self.s_req.connect(PORT_REQ)
    
    def send_request(self, category, action, request_content):
        request_id = "%s.%s.%s.%s.%s" %(REQ_PREFIX, str(time.time()).replace('.','_'), category, action, MSG_VERSION)
        request = {'id': request_id, 'content': request_content}
        self.s_req.send(json.dumps(request))
        print("\nRequest sent : %s, waiting for reply..." % request)
        
        reply = self.s_req.recv()

        return reply

class MessagingRep(MessagingReqRep):
    def __init__(self):
        MessagingReqRep.__init__(self)
        self.s_rep = self.context.socket(zmq.REP)
        self.s_rep.connect(PORT_REP)
    
    def wait_for_request(self):
        self.j_request = self.s_rep.recv() # JSON is received
        return self.j_request
    
    def send_reply(self, reply_content):
        request = json.loads(self.j_request)
        raw_request_id = request['id'][len(REQ_PREFIX)+1:] # remove request prefix
        reply_id = "%s.%s" % (REP_PREFIX, raw_request_id)
        reply = {'id': reply_id, 'content': reply_content}
        self.s_rep.send(json.dumps(reply))
        print("Reply sent : %s\n" % reply)
        
