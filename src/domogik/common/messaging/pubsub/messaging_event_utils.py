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
from time import sleep, time
from domogik.common import logger
from domogik.common.configloader import Loader

MSG_VERSION = "0_1"

class MessagingEvent:
    def __init__(self, caller_id):
        if caller_id is None:
            raise Exception("Caller id can't be empty!")
        self.caller_id = caller_id
        self.context = zmq.Context()
        cfg = Loader('messaging').load()
        self.cfg_messaging = dict(cfg[1])

class MessagingEventPub(MessagingEvent):
    def __init__(self, caller_id):
        MessagingEvent.__init__(self, caller_id)
        self.log = logger.Logger('messaging_event_pub').get_logger()
        self.s_send = self.context.socket(zmq.PUB)
        self.s_send.connect("tcp://localhost:%s" % self.cfg_messaging['event_pub_port'])
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
        #msg = json.dumps({'id': msg_id, 'content': content})
        self.s_send.send(msg_id, zmq.SNDMORE)
        self.s_send.send(content)
        self.log.debug("%s : id = %s - content = %s" % (self.caller_id, msg_id, content))

class MessagingEventSub(MessagingEvent):
    def __init__(self, caller_id, category_filter=None):
        MessagingEvent.__init__(self, caller_id)
        self.log = logger.Logger('messaging_event_sub').get_logger()
        self.s_recv = self.context.socket(zmq.SUB)
        self.s_recv.connect("tcp://localhost:%s" % self.cfg_messaging['event_sub_port'])
        topic_filter = ''
        if category_filter is not None:
            topic_filter = category_filter
        self.log.debug("%s : topic filter : %s" % (self.caller_id, topic_filter))
        self.s_recv.setsockopt(zmq.SUBSCRIBE, topic_filter)
    
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
            self.log.error("Message not complete (content is missing)!")
            return None
