#!/usr/bin/python
# -*- coding: utf-8 -*-

# Utility class for request / reply pattern

import zmq
import time
import json
from json import JSONEncoder
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


class MqMsg:
    """ Manage Mq messages, convert from/to JSON/obj to obj/JSON
    """
    def __init__(self, msg=None):
        """ Load object from JSON if object exists
        @param msg : json representaion of the Message
        """

    def from_json(self, msg):
        """ Load object from JSON
        @param msg : json representaion of the Message
        """

        o = json.loads(msg, object_hook=as_python_object)
        self.id = o['id']
        self.raw_id = self.id[len(REQ_PREFIX) + 1:]
        self.type, self.category, self. action, self.timestamp, self.version = o['id'].split('.')
        self.content = o['content']

    def from_obj(self, type, category, action, timestamp, version, content):
        """ Load Message from object
        @param type : Message's type (req/rep)
        @param category : Message's category
        @param action : Message's action
        @param timestamp : Messages's timestamp
        @param version : Protocol minimal supported version
        @param content : Payload of message
        """
        self.type = type
        self.category = category
        self.action = action
        self.timestamp = timestamp
        self.version = version
        self.id = "%s.%s.%s.%s.%s" % (type, category, action, timestamp, version)
        self.content = content

    def as_obj(self):
        """ Return message as object
        @return a tuple (type, category, action, timestamp, version, content)
        """
        return self.type, self.category, self.action, self.timestamp, self.version, self.content

    def as_json(self):
        """ Return message as JSON
        @return a JSON valid string which represents the message
        """
        return json.dumps({'id': self.id, 'content': self.content}, cls=PythonObjectEncoder)


class MqReqRep:
    def __init__(self):
        self.context = zmq.Context()


class MqReq(MqReqRep):
    def __init__(self):
        MqReqRep.__init__(self)
        self.s_req = self.context.socket(zmq.REQ)
        self.s_req.connect(PORT_REQ)

    def send_request(self, category, action, request_content):
        req = MqMsg()
        req.from_obj(REQ_PREFIX, category, action, str(time.time()).replace('.', '_'), MSG_VERSION)
        request = req.to_json()
        self.s_req.send(request)
        print("\nRequest sent : %s, waiting for reply..." % request)

        reply = self.s_req.recv()

        return reply


class MqRep(MqReqRep):
    def __init__(self):
        MqReqRep.__init__(self)
        self.s_rep = self.context.socket(zmq.REP)
        self.s_rep.connect(PORT_REP)
        self.j_request = None  # JSON version of message
        self.o_request = None  # Object version of message

    def wait_for_request(self):
        """ Wait for a request from MQ
        @returns json_version, object_version
        """
        self.j_request = self.s_rep.recv()  # JSON is received
        self.o_request = MqMsg(self.j_request)
        return self.j_request, self.o_request

    def send_reply(self, reply_content):
        reply = MqMsg()
        reply.id = "%s.%s" % (REP_PREFIX, self.o_request.raw_id)
        reply.content = reply_content
        self.s_rep.send(reply.to_json())
        print("Reply sent : %s\n" % reply.to_json())
