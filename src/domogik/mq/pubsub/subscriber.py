#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

Utility class for publish / subscribe pattern

Implements
==========


@author: Marc SCHNEIDER <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import json
import zmq
import sys
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop
try:
    from domogik.common.configloader import Loader
except ImportError:
    from domoweb.models import Parameter

MSG_VERSION = "0_1"

class MQSyncSub():
    def __init__(self, context, caller_id, category_filters):
        if ("domogik.common.configloader" in sys.modules):
            cfg = Loader('mq').load()
            self.cfg_mq = dict(cfg[1])
            sub_addr = "tcp://{0}:{1}".format(self.cfg_mq['ip'], self.cfg_mq['sub_port'])
        else:
            ipaddr = Parameter.objects.get(key='mq-ip')
            port = Parameter.objects.get(key='mq-sub_port')
            sub_addr = "tcp://{0}:{1}".format(ipaddr.value, port.value)
        self.s_recv = context.socket(zmq.SUB)
        self.caller_id = caller_id
        self.s_recv.connect(sub_addr)

        for category_filter in category_filters:
            self.s_recv.setsockopt(zmq.SUBSCRIBE, category_filter)
        if len(category_filters) == 0:
            self.s_recv.setsockopt(zmq.SUBSCRIBE, '')
    
    def __del__(self):
        # Not sure this is really mandatory
        self.s_recv.close()
    
    def wait_for_event(self):
        """Receive an event

        @return : a dict with two keys : id and content (which should be in JSON format)

        """
        msg_id = self.s_recv.recv()
        more = self.s_recv.getsockopt(zmq.RCVMORE)
        if more:
            msg_content = self.s_recv.recv(zmq.RCVMORE)
            return {'id': msg_id, 'content': msg_content}
        else:
            msg_error = "Message not complete (content is missing)!, so leaving..."
            raise Exception(msg_error)

class MQAsyncSub():
    def __init__(self, context, caller_id, category_filters):
        if ("domogik.common.configloader" in sys.modules):
            cfg = Loader('mq').load()
            self.cfg_mq = dict(cfg[1])
            sub_addr = "tcp://{0}:{1}".format(self.cfg_mq['ip'], self.cfg_mq['sub_port'])
        else:
            ipaddr = Parameter.objects.get(key='mq-ip')
            port = Parameter.objects.get(key='mq-sub_port')
            sub_addr = "tcp://{0}:{1}".format(ipaddr.value, port.value)
        self.caller_id = caller_id
        self.s_recv = context.socket(zmq.SUB)
        self.s_recv.connect(sub_addr)

        if len(category_filters) == 0:
            self.s_recv.setsockopt(zmq.SUBSCRIBE, '')
        else:
            for category_filter in category_filters:
                self.s_recv.setsockopt(zmq.SUBSCRIBE, category_filter)
        ioloop = IOLoop.instance()
        self.stream = ZMQStream(self.s_recv, ioloop)
        self.stream.on_recv(self._on_message)
    
    def __del__(self):
        # Not sure this is really mandatory
        self.s_recv.close()
    
    def _on_message(self, msg):
        """Received an event
        will lookup the correct callback to use, and call it
        
        :param: msg = the message received
        """
        mid = msg[0]
        mid = mid.split('.')
        # delete msg version
        del mid[-1]
        # delete timestamp
        del mid[-1]
        # build up the id again
        mid = '.'.join(mid)

	try:
	    jsons = json.loads(msg[1])
            self.on_message(mid, jsons)
        except ValueError as e:
            pass
  
    def on_message(self, msg_id, content):
        """Public method called when a message arrived.

        .. note:: Does nothing. Should be overloaded!
        """
        pass
