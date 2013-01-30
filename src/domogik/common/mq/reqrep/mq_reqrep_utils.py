#!/usr/bin/python
# -*- coding: utf-8 -*-

# Utility class for request / reply pattern

import zmq
import time
import json
from json import dumps, loads, JSONEncoder, JSONDecoder
import pickle

MSG_VERSION = "0_1"
PORT_REQ = "tcp://localhost:6559"
PORT_REP = "tcp://localhost:6560"

REQ_PREFIX = "req"
REP_PREFIX = "rep"

class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return JSONEncoder.default(self, obj)
        return {'_python_object': pickle.dumps(obj)}

def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(str(dct['_python_object']))
    return dct

class MqReqRep:
    def __init__(self):
        self.context = zmq.Context()

class MqReq(MqReqRep):
    def __init__(self):
        MqReqRep.__init__(self)
        self.s_req = self.context.socket(zmq.REQ)
        self.s_req.connect(PORT_REQ)

    def send_request(self, category, action, request_content):
        request_id = "%s.%s.%s.%s.%s" %(REQ_PREFIX, category, action, str(time.time()).replace('.','_'), MSG_VERSION)
        request = {'id': request_id, 'content': request_content}
        self.s_req.send(json.dumps(request, cls=PythonObjectEncoder))
        print("\nRequest sent : %s, waiting for reply..." % request)

        reply = self.s_req.recv()

        return reply

class MqRep(MqReqRep):
    def __init__(self):
        MqReqRep.__init__(self)
        self.s_rep = self.context.socket(zmq.REP)
        self.s_rep.connect(PORT_REP)

    def wait_for_request(self):
        self.j_request = self.s_rep.recv() # JSON is received
        return self.j_request

    def send_reply(self, reply_content):
        request = json.loads(self.j_request, object_hook=as_python_object)
        raw_request_id = request['id'][len(REQ_PREFIX)+1:] # remove request prefix
        reply_id = "%s.%s" % (REP_PREFIX, raw_request_id)
        reply = {'id': reply_id, 'content': reply_content}
        self.s_rep.send(json.dumps(reply, cls=PythonObjectEncoder))
        print("Reply sent : %s\n" % reply)

