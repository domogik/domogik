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
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, DelayedCallback
from time import sleep, time
from domogik.common import logger
from domogik.common.configloader import Loader

MSG_VERSION = "0_1"

class MqEvent:
    def __init__(self, context, caller_id):
        if caller_id is None:
            raise Exception("Caller id can't be empty!")
        self.caller_id = caller_id
        self.context = context
        cfg = Loader('mq').load()
        self.cfg_mq = dict(cfg[1])

class MqPub(MqEvent):
    def __init__(self, context, caller_id):
        MqEvent.__init__(self, context, caller_id)
        self.log = logger.Logger('mq_event_pub').get_logger()
        self.s_send = self.context.socket(zmq.PUB)
        pub_addr= "tcp://{0}:{1}".format(self.cfg_mq['mq_ip'], self.cfg_mq['event_pub_port'])
        self.log.debug("Publishing on address : %s" % pub_addr)
        self.s_send.connect(pub_addr)
        # TODO : change me! this is a dirty trick so that the first message is not lost by the receiver
        # but is not reliable as it depends on machine/network latency
        sleep(1)

    def __del__(self):
        # Not sure this is really mandatory
        self.s_send.close()

    def send_event(self, category, content):
        """Send an event in in multi-part : first message id and then its content

        @param category : category of the message
        @param content : content of the message : must be in JSON format

        """
        msg_id = "%s.%s.%s" %(category, str(time()).replace('.','_'), MSG_VERSION)
        self.s_send.send(msg_id, zmq.SNDMORE)
        self.s_send.send(content)
        self.log.debug("%s : id = %s - content = %s" % (self.caller_id, msg_id, content))

class MqSyncSub(MqEvent):
    def __init__(self, context, caller_id, *category_filters):
        MqEvent.__init__(self, context, caller_id)
        self.log = logger.Logger('mq_event_sub').get_logger()
        self.s_recv = self.context.socket(zmq.SUB)
        sub_addr= "tcp://{0}:{1}".format(self.cfg_mq['mq_ip'], self.cfg_mq['event_sub_port'])
        self.log.debug("Subscribing to address : %s" % sub_addr)
        self.s_recv.connect(sub_addr)

        for category_filter in category_filters:
            self.log.debug("%s : category filter : %s" % (self.caller_id, category_filter))
            self.s_recv.setsockopt(zmq.SUBSCRIBE, category_filter)
        if len(category_filters) == 0:
            self.log.debug('No filter')
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
            self.log.debug("%s : id = %s - content = %s" % (self.caller_id, msg_id, msg_content))
            return {'id': msg_id, 'content': msg_content}
        else:
            msg_error = "Message not complete (content is missing)!, so leaving..."
            self.log.error(msg_error)
            raise Exception(msg_error)

class MqAsyncSub(MqEvent):
    def __init__(self, context, caller_id, category_filters):
        """
        :param category_filters: a dictionary with the key equal to the filter and the value equal to the callback
        """
        MqEvent.__init__(self, context, caller_id)
        self.log = logger.Logger('mq_event_sub').get_logger()
        self.s_recv = self.context.socket(zmq.SUB)
        sub_addr= "tcp://{0}:{1}".format(self.cfg_mq['mq_ip'], self.cfg_mq['event_sub_port'])
        self.log.debug("Subscribing to address : %s" % sub_addr)
        self.s_recv.connect(sub_addr)

        if len(category_filters) == 0:
	    self.log.debug("%s : with no category filter(s)" % (self.caller_id))
	    self.s_recv.setsockopt(zmq.SUBSCRIBE, '')
        else:
            for category_filter in category_filters:
	        self.log.debug("%s : category filter : %s" % (self.caller_id, category_filter))
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
        self.log.debug("%s : id = %s - content = %s" % (self.caller_id, msg[0], msg[1]))
        self.on_message(msg[0], msg[1])
  
    def on_message(self, msg_id, content):
        """Public method called when a message arrived.

        .. note:: Does nothing. Should be overloaded!
        """
        pass
