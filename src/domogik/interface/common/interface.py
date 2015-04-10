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

Plugin purpose
==============

Base class for all xPL clients

Implements
==========

- Interface

@author: Fritz SMH <fritz.smg@gmail.com> 
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import signal
import threading
import os
import sys
from domogik.common.plugin import Plugin
from domogikmq.pubsub.publisher import MQPub
import traceback
import zmq

# interface vendor id
INTERFACE_VENDOR_ID = "interface"

class Interface(Plugin):
    '''
    For interfaces clients
    '''


    def __init__(self, name, stop_cb = None, is_manager = False, parser = None,
                 daemonize = True, log_prefix = "interface_", test = False, source = None):
        '''
        Create Interface instance, which defines system handlers
        @param source : overwrite the source value (client-device.instance)
        '''

        Plugin.__init__(self, name, type = "interface", stop_cb = stop_cb, is_manager = is_manager, parser = parser, daemonize = daemonize, log_prefix = log_prefix, test = test)

        self.log.info(u"Start of the interface init")
        # define the source (in can be used in some plugins)
        if source == None:
            self.source = "{0}-{1}.{2}".format(INTERFACE_VENDOR_ID, self.get_plugin_name(), self.get_sanitized_hostname())
        # in case we overwrite the source : 
            self.source = source

        ### MQ
        self._mq_name = self.source
        self.zmq = zmq.Context()
        self.mq_pub = MQPub(self.zmq, self._mq_name)

        ### Context
        # set the context
        # All elements that may be added in the request sent over MQ
        # * media (irc, audio, sms, ...)
        # * text (from voice recognition)
        # * location (the input element location : this is configured on the input element : kitchen, garden, bedroom, ...)
        # * identity (from face recognition)
        # * mood (from kinect or anything else) 
        # * sex (from voice recognition and post processing on the voice)
        self.context = {"media" : None,
                        "location" : None,
                        "identity" : self.source,
                        "mood" : None,
                        "sex" : None
                       }
        self.log.info(u"End of the interface init")


    def send_to_butler(self, message):
        """ Send a message over MQ to the butler component
        """
        self.log.info("Send a message to the butler : {0}".format(message))
        request = self.context
        request["text"] = message
        self.mq_pub.send_event('interface.input',
                             request)


    def on_message(self, msgid, content):
        """ When a message is received from the MQ (pub/sub)
        """
        if msgid == "interface.output":
            self.log.debug("interface.output received message : {0}".format(content))
            return

            ### filter on location, media
            # if media not cli, don't process
            if content['media'] != "cli": 
                return
            # location
            # no location, so no check

            ### Display message in the cli
            #print("{0}".format(content['text']))
            print(u"{0} > {1}".format(BUTLER_CLI_NAME, content['text']))

            ### Display the prompt for the next exchange
            print("{0} > ".format(BUTLER_CLI_USER))
