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

- XplPlugin

@author: Maxence Dunnewind <maxence@dunnewind.net>
         Fritz SMH <fritz.smg@gmail.com> for refactoring
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import signal
import threading
import os
import sys
from domogik.xpl.common.xplconnector import XplMessage, Manager, Listener
from domogik.common.plugin import Plugin
import traceback

# domogik vendor id (for xpl)
DMG_VENDOR_ID = "domogik"

class XplPlugin(Plugin):
    '''
    Global plugin class, manage signal handlers.
    This class shouldn't be used as-it but should be extended by xPL plugin
    This class is a Singleton
    '''


    def __init__(self, name, stop_cb = None, is_manager = False, parser = None,
                 daemonize = True, log_prefix = "xplplugin_", log_on_stdout = True, test = False, nohub = False, source = None):
        '''
        Create XplPlugin instance, which defines system handlers
        @param nohub : if set the hub discovery will be disabled
        @param source : overwrite the source value (client-device.instance)
        '''

        Plugin.__init__(self, name, stop_cb = stop_cb, is_manager = is_manager, parser = parser, daemonize = daemonize, log_prefix = log_prefix, log_on_stdout = log_on_stdout, test = test)

        ### start xpl dedicated part

        self.log.info(u"Start of the xPL init")

        # start the xPL manager
        if 'broadcast' in self.config:
            broadcast = self.config['broadcast']
        else:
            broadcast = "255.255.255.255"
        if 'bind_interface' in self.config:
            self.myxpl = Manager(self.config['bind_interface'], broadcast = broadcast, plugin = self, nohub = nohub, source = source)
        else:
            self.myxpl = Manager(broadcast = broadcast, plugin = self, nohub = nohub)

        # hbeat not yet called (will be called by the ready() function by a developper plugin)
        self.enable_hbeat_called = False

        # define the source (in can be used in some plugins)
        if source == None:
            self.source = "{0}-{1}.{2}".format(DMG_VENDOR_ID, self.get_plugin_name(), self.get_sanitized_hostname())
        # in case we overwrite the source :
            self.source = source
        self.log.info(u"End of the xPL init")



    def ready(self, ioloopstart=1):
        """ to call at the end of the __init__ of classes that inherits of XplPlugin
        """
        ### First, Do only the xPL related tasks

        # activate xpl hbeat
        if self.enable_hbeat_called == True:
            self.log.error(u"in ready() : enable_hbeat() function already called : the plugin may not be fully converted to the 0.4+ Domogik format")
        else:
            self.enable_hbeat()

        # send the status for the xpl hbeat
        self.myxpl.update_status(2)

        ### finally call the function from the Plugin class to do the common things
        # this is called as the end ad the MQ IOLoop is a blocking call
        Plugin.ready(self, ioloopstart)



    def enable_hbeat(self, lock = False):
        """ Wrapper for xplconnector.enable_hbeat()
        """
        self.myxpl.enable_hbeat(lock)
        self.enable_hbeat_called = True

    # TODO : reactivate later
    #        maybe will use the MQ instead
    #def _send_process_info(self, pid, data):
    #    """ Send process info (cpu, memory) on xpl
    #        @param : process pid
    #        @param data : dictionnary of process informations
    #    """
    #    mess = XplMessage()
    #    mess.set_type("xpl-stat")
    #    mess.set_schema("domogik.usage")
    #    mess.add_data({"name" : "%s.%s" % (self.get_plugin_name(), self.get_sanitized_hostname()),
    #                   "pid" : pid,
    #                   "cpu-percent" : data["cpu_percent"],
    #                   "memory-percent" : data["memory_percent"],
    #                   "memory-rss" : data["memory_rss"],
    #                   "memory-vsz" : data["memory_vsz"]})
    #    self.myxpl.send(mess)


    def _send_hbeat_end(self):
        """ Send the hbeat.end message
        """
        if hasattr(self, "myxpl"):
            mess = XplMessage()
            mess.set_type("xpl-stat")
            mess.set_schema("hbeat.end")
            self.myxpl.send(mess)

    def wait(self):
        """ Wait until someone ask the plugin to stop
        """
        self.myxpl._network.join()

    def force_leave(self, status = False, return_code = None, exit=True):
        """ Leave threads & timers
        """
        ### Do the xPL related tasks

        # send hbeat.end message
        self._send_hbeat_end()

        ### finally call the function from the Plugin class to do the common things
        # this is called as the end ad the MQ IOLoop is a blocking call
        Plugin.force_leave(self, status, return_code, exit)


