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

Purpose
=======

Tools for regression tests

Usage
=====

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import zmq
from domogik.xpl.common.plugin import STATUS_ALIVE
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.pubsub.subscriber import MQSyncSub
from domogik.mq.message import MQMessage

class TestPlugin():
    """ Handle some actions on the plugins to test them
    """

    def __init__(self, name, host):
        """ Constructor
            @param name: plugin name
            @param host: plugin host
        """
        self.name = name
        self.host = host

    def request_startup(self):
        """ Request the plugin to start over the manager
        """
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.start.do')
        msg.add_data('name', 'diskfree')
        result = cli.request('manager', msg.get(), timeout=10) 
        if result:
            print(result.get())
            return True
        else:
            raise RuntimeError("MQ Timeout when requesting manager to start the plugin")

    def wait_for_startup(self, timeout = 30):
        """ Wait for a plugin to be completely started
            This is done by subscribing on the MQ plugin.status publisher
            If no status '' has been catched before the timeout, raise an error
        """
        sub = MQSyncSub(zmq.Context(), 'test', ['plugin.status'] )
        result = sub.wait_for_event()
        if result is not None:
            reply = json.loads(stat['content'])
            print(reply)
        else:
            raise RuntimeError("MQ Timeout when waiting for the plugin to be in state 'STATUS_ALIVE'")

