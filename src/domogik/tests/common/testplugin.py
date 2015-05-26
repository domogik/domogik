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
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.pubsub.subscriber import MQAsyncSub
from domogikmq.message import MQMessage
from domogik.common.plugin import STATUS_ALIVE, STATUS_STOPPED
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
        self.count = 0
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['plugin.status'])

    def request_startup(self):
        """ Request the plugin to start over the manager
        """
        print(u"Request plugin startup to the manager for '{0}' on '{1}'".format(self.name, self.host))
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.start.do')
        msg.add_data('type', "plugin")
        msg.add_data('name', self.name)
        msg.add_data('host', self.host)
        result = cli.request('manager', msg.get(), timeout=10) 
        if result:
            msgid, content = result.get()
            content = json.loads(content)
            print(u"Response from the manager : {0}".format(content))
            if content['status']:
                print(u"Plugin started")
                return True
            else:
                print(u"Error : plugin not started")
                return False
        else:
            raise RuntimeError("MQ Timeout when requesting manager to start the plugin")

    def request_stop(self):
        """ Request the plugin to stop
        """
        print(u"Request plugin to stop : '{0}' on '{1}'".format(self.name, self.host))
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.stop.do')
        msg.add_data('type', "plugin")
        msg.add_data('name', self.name)
        msg.add_data('host', self.host)
        result = cli.request("plugin-{0}.{1}".format(self.name, self.host), msg.get(), timeout=10) 
        return True
        # TODO : reactivate this code
        # for a unknown reason, the timeout is always reached even if we can see the plugin.stop.result in the MQ logs
        # so as this feature is a blocking point to allow packages tests, for now we comment the check on this part 
        # and assume the plugin has responded to the plugin.stop.do response.
        # The real check is done in wait_for_event() by catching the stop event
        #if result:
        #    msgid, content = result.get()
        #    content = json.loads(content)
        #    print(u"Response : {0}".format(content))
        #    if content['status']:
        #        print(u"Plugin stopped")
        #        return True
        #    else:
        #        print(u"Error : plugin not stopped")
        #        return False
        #else:
        #    raise RuntimeError("MQ Timeout when requesting to stop the plugin (the plugin didn't stop itself)")

    def wait_for_event(self, event, timeout = 60):
        """ Wait for a plugin to be in a state
            @param event : the event (STATUS_ALIVE, STATUS_STOPPED, ...)
            @param timeout : timeout for the MQ
            This is done by subscribing on the MQ plugin.status publisher
            If no status has been catched before the timeout, raise an error
        """
        self.count = 0
        print(u"Start listening to MQ...")
        IOLoop.instance().start() 
        # TODO : handle timeout

        # the following line will be processed when a IOLoop.instance().stop() will be called
        if self.plugin_status == event:
            print(u"Event '{0}' detected".format(event))
            return True
        else:
            print(u"Plugin not in status '{0}' : status = {1}".format(event, self.plugin_status))
            return False

    def on_message(self, msgid, content):
        """ Handle MQ messages
            @param msgid : message id
            @content : message content
        """
        if msgid == "plugin.status":
            # we may miss starting and stop-request events but we only want to do some checks on alive and stopped...
            # and sometimes it happens that we still receive a last 'alive' status before the 'stop' one
            if self.count == 0:
                print(u"Message skipped (we skip the first one) : msgid={0}, content={1}".format(msgid, content))
                self.count = 1
                return 

            print(u"Message received : msgid={0}, content={1}".format(msgid, content))
            if content['name'] == self.name and \
               content['type'] == self.type and \
               content['host'] == self.host:
                self.plugin_status = content['event']
                # plugin started
                if content['event'] == STATUS_ALIVE:
                    print(u"Plugin is started")
                    print(u"Stop listening to MQ as we get our result")
                    IOLoop.instance().stop() 
    
                # plugin stopped
                elif content['event'] == STATUS_STOPPED:
                    print(u"Plugin is stopped")
                    print(u"Stop listening to MQ as we get our result")
                    IOLoop.instance().stop() 
         

