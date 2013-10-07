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
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
#from domogik.mq.pubsub.subscriber import MQSyncSub
from domogik.mq.pubsub.subscriber import MQAsyncSub
from domogik.mq.message import MQMessage
from domogik.xpl.common.plugin import STATUS_ALIVE, STATUS_STOPPED
import json

class TestPlugin(MQAsyncSub):
    """ Handle some actions on the plugins to test them
    """

    def __init__(self, name, host):
        """ Constructor
            @param name: plugin name
            @param host: plugin host
        """
        self.name = name
        self.host = host
        self.type = "plugin"
        self.plugin_status = None
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['plugin.status'])

    def request_startup(self):
        """ Request the plugin to start over the manager
        """
        print("Request plugin startup to the manager for '{0}' on '{1}'".format(self.name, self.host))
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.start.do')
        msg.add_data('name', self.name)
        msg.add_data('host', self.host)
        result = cli.request('manager', msg.get(), timeout=10) 
        if result:
            msgid, content = result.get()
            content = json.loads(content)
            print("Response from the manager : {0}".format(content))
            if content['status']:
                print("Plugin started")
                return True
            else:
                print("Error : plugin not started")
                return False
        else:
            raise RuntimeError("MQ Timeout when requesting manager to start the plugin")

    def request_stop(self):
        """ Request the plugin to stop
        """
        print("Request plugin to stop : '{0}' on '{1}'".format(self.name, self.host))
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.stop.do')
        msg.add_data('name', self.name)
        msg.add_data('host', self.host)
        result = cli.request("plugin-{0}.{1}".format(self.name, self.host), msg.get(), timeout=10) 
        if result:
            msgid, content = result.get()
            content = json.loads(content)
            print("Response : {0}".format(content))
            if content['status']:
                print("Plugin stopped")
                return True
            else:
                print("Error : plugin not stopped")
                return False
        else:
            raise RuntimeError("MQ Timeout when requesting to stop the plugin")

    def wait_for_event(self, event, timeout = 30):
        """ Wait for a plugin to be in a state
            @param event : the event (STATUS_ALIVE, STATUS_STOPPED, ...)
            This is done by subscribing on the MQ plugin.status publisher
            If no status has been catched before the timeout, raise an error
        """
        print("Start listening to MQ...")
        IOLoop.instance().start() 
        # TODO : handle timeout

        # the following line will be processed when a IOLoop.instance().stop() will be called
        if self.plugin_status == event:
            return True
        else:
            print("Plugin not in status '{0}' : status = {1}".format(event, self.plugin_status))
            return False

    def on_message(self, msgid, content):
        """ Handle MQ messages
            @param msgid : message id
            @content : message content
        """
        if msgid == "plugin.status":
            print("Message received : msgid={0}, content={1}".format(msgid, content))
            self.plugin_status = content['event']
            if content['name'] == self.name and \
               content['type'] == self.type and \
               content['host'] == self.host:
                # plugin started
                if content['event'] == STATUS_ALIVE:
                    print("Plugin is started")
                    print("Stop listening to MQ as we get our result")
                    IOLoop.instance().stop() 
    
                # plugin stopped
                elif content['event'] == STATUS_STOPPED:
                    print("Plugin is stopped")
                    print("Stop listening to MQ as we get our result")
                    IOLoop.instance().stop() 
         

