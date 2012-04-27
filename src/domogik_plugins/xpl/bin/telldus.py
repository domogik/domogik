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
xPL client through the TellStick and Tellstick Duo

Support Chacon/DIO, Nexa, Proove, Intertechno, HomeEasy, KlikAanKlikUit,
Byebye Standby, Rusta ... and many others
For a list of supported protocols/models, please see the telldus-core
documentation here : http://developer.telldus.se/wiki/TellStick_conf

Implements
==========

- telldus.__init__(self)
- telldus.telldus_cmnd_cb(self, message)
- telldus.telldus_monitor_cb(self, house, unit, order, args = None)
- telldus.send_xpl(self, house, unit, order, args = None):

Thanks to :
Julien Garet <julien@garet.info>
@author: Sebastien GALLET <sgallet@gmail.com>
@license: GPL(v3)
@copyright: (C) 2007-2009 Domogik project
"""

import traceback

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik_plugins.xpl.lib.telldus import *
import os.path
import sys
import traceback
import logging
logging.basicConfig()

class telldus(XplPlugin):
    '''
    Manage chacon devices through the TellStick device
    '''
    def __init__(self):
        """
        Create the telldus class
        This class is used to connect devices (through telldus) to the xPL Network
        """
        XplPlugin.__init__(self, name = 'telldus',reload_cb = self.telldus_reload_config_cb)
        self.log.info("telldus.__init__ : Start ...")
        self.log.debug("telldus.__init__ : Try to start the telldus librairy")
        self._device = "/dev/tellstick"
        #Check if the device exists
        if not os.path.exists(self._device):
            self.log.warning(self._device + " is not present but Tellstick Duo don't use it.")
        else:
            self.log.debug("Device present as "+self._device)
        self._config = Query(self.myxpl, self.log)
        try:
            self._mytelldus = telldusAPI(self.send_xpl,self.log,self._config,self.myxpl)
        except Exception:
            self.log.exception("Something went wrong during telldus init, check logs")
            exit(1)
        #Create listeners
        self.log.debug("telldus.__init__ : Create listeners")
        Listener(self.telldus_cmnd_cb, self.myxpl,
                 {'schema': 'telldus.basic', 'xpltype': 'xpl-cmnd'})
        Listener(self.telldus_reload_config_cb, self.myxpl,
                 {'schema': 'domogik.system', 'xpltype': 'xpl-cmnd',
                  'command': 'reload', 'plugin': 'telldus'})
        self.enable_hbeat()
        self.log.info("Telldus plugin correctly started")

    def telldus_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        commands = {
            'on': lambda hu, l: self._mytelldus.sendOn(hu),
            'off': lambda hu, l: self._mytelldus.sendOff(hu),
            'dim': lambda hu, l: self._mytelldus.sendDim(hu,l),
            'bright': lambda hu, l: self._mytelldus.sendBright(hu,l),
            'up': lambda hu, l: self._mytelldus.sendUp(hu),
            'down': lambda hu, l: self._mytelldus.sendDown(hu),
            'stop': lambda hu, l: self._mytelldus.sendStop(hu),
            'shut': lambda hu, l: self._mytelldus.sendShut(hu,l),
        }
        try :
            cmd = None
            if 'command' in message.data:
                cmd = message.data['command']
            device = None
            if 'device' in message.data:
                device = message.data['device']
            level = None
            if 'level' in message.data:
                level = message.data['level']

            self.log.debug("%s received : device= %s, level=%s" %
                           (cmd, device,level))
            commands[cmd](device, level)
            self.telldus_monitor_cb(device, cmd)
        except:
            self.log.error("action _ %s _ unknown."%(request))
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self.log.info("TelldusException : "+error)

    def telldus_monitor_cb(self, add, order, args = None):
        """
        Callback for telldus monitoring
        @param add : address ot the module
        @param order : the order sent to the unit
        """
        self.log.debug("Telldus Callback YEDfor %s" % add)
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("telldus.basic")
        mess.add_data({"device" :  add})
        mess.add_data({"command" :  order})
        if args:
            mess.add_data({"level" : args})
        self.myxpl.send(mess)


    def telldus_reload_config_cb(self):
        """
        Callback for telldus reload config
        @param message : xpl message
        """
        self.log.debug("Telldus reload config received")
        self._mytelldus.reload()

    def send_xpl(self, add, order, args = None):
        """
        Callback for sending xpl
        @param add : address of the module
        @param order : the order sent to the unit
        """
        self.log.debug("Telldus send_xpl for %s" % add)
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("telldus.basic")
        mess.add_data({"device" :  add})
        mess.add_data({"command" :  order})
        if args:
            mess.add_data({"level" : args})
        self.myxpl.send(mess)

if __name__ == "__main__":
    telldus()
