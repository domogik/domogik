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
@copyright: (C) 2007-2012 Domogik project
"""

from domogik.xpl.common.xplconnector import Listener
#from domogik.xpl.common.xplmessage import XplMessage
#from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.telldus import TelldusAPI
import traceback
try :
    from domogik_packages.xpl.lib.helperplugin import XplHlpPlugin
except :
    print "Cant load helper plugin : "
    print traceback.format_exc()
try :
    from domogik_packages.xpl.lib.lightplugin import LightingExtension
except :
    print "Cant load lighting extension (not a problem if you don't use it) : "
    print traceback.format_exc()
import os.path
import traceback
#import logging
#logging.basicConfig()

class Telldus(XplHlpPlugin):
    '''
    Manage chacon devices through the TellStick device
    '''
    def __init__(self):
        """
        Create the telldus class
        This class is used to connect devices (through telldus) to
        the xPL Network
        """
        XplHlpPlugin.__init__(self, name = 'telldus',
            reload_cb = self.telldus_reload_config_cb)
        self.log.info("telldus.__init__ : Start ...")
        self.log.debug("telldus.__init__ : Try to start the telldus library")
        self._device = "/dev/tellstick"
        #Check if the device exists
        if not os.path.exists(self._device):
            self.log.warning(self._device +
                " is not present but Tellstick Duo don't use it.")
        else:
            self.log.debug("Device present as "+self._device)
        self._config = Query(self.myxpl, self.log)
        try:
            self._mytelldus = TelldusAPI(self.send_xpl, self.log,
                self._config)
        except Exception:
            self.log.error("Something went wrong during telldus "+
                "init, check logs")
            self.force_leave()
            exit(1)
        #Create listeners
        self.log.debug("telldus.__init__ : Create listeners")
        Listener(self.telldus_cmnd_cb, self.myxpl,
                 {'schema': 'telldus.basic', 'xpltype': 'xpl-cmnd'})
        Listener(self.telldus_reload_config_cb, self.myxpl,
                 {'schema': 'domogik.system', 'xpltype': 'xpl-cmnd',
                  'command': 'reload', 'plugin': 'telldus'})
        try:
            boo = self._config.query('telldus', 'lightext')
            if boo == None:
                boo = "False"
            self._lightext = eval(boo)
        except:
            self.log.warning("Can't get delay configuration from XPL. Disable lighting extensions.")
            self._lightext = False
        if self._lightext == True:
            self._lighting = LightingExtension(self, self._name, \
                self._mytelldus.lighting_activate_device, \
                self._mytelldus.lighting_deactivate_device, \
                self._mytelldus.lighting_valid_device)

        self.helpers =   \
           { "list" :
              {
                "cb" : self._mytelldus.helpers.helper_list,
                "desc" : "List devices in telldus daemon.",
                "usage" : "list [devicetype]",
                "param-list" : "devicetype",
                "min_args" : 0,
                "devicetype" : "devicetype : the type of device to find",
              },
             "info" :
              {
                "cb" : self._mytelldus.helpers.helper_info,
                "desc" : "Display device information",
                "usage" : "info <device>",
                "param-list" : "device",
                "min_args" : 1,
                "device" : "device address",
              },
            }
        if self._lightext == True:
            self._lighting.enable_lighting()
        self.enable_helper()
        self.enable_hbeat()
        self.log.info("Telldus plugin correctly started")

    def telldus_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        commands = {
            'on': lambda hu, l, f: self._mytelldus.send_on(hu),
            'off': lambda hu, l, f: self._mytelldus.send_off(hu),
            'dim': lambda hu, l, f: self._mytelldus.send_dim(hu, l),
            'bright': lambda hu, l, f: self._mytelldus.send_bright(hu, l, f),
            'shine': lambda hu, l, f: self._mytelldus.send_shine(hu, l, f),
            'change': lambda hu, l, f: self._mytelldus.send_change(hu, l, f),
            'up': lambda hu, l, f: self._mytelldus.send_up(hu),
            'down': lambda hu, l, f: self._mytelldus.send_down(hu),
            'stop': lambda hu, l, f: self._mytelldus.send_stop(hu),
            'shut': lambda hu, l, f: self._mytelldus.send_shut(hu, l),
        }
        try :
            cmd = None
            if 'command' in message.data:
                cmd = message.data['command']
            device = None
            if 'device' in message.data:
                device = message.data['device']
            level = "0"
            if 'level' in message.data:
                level = message.data['level']
            faderate = "0"
            if 'faderate' in message.data:
                faderate = message.data['faderate']
            self.log.debug("%s received : device= %s, level=%s" %
                           (cmd, device, level))
            commands[cmd](device, level, faderate)
        except Exception:
            self.log.error("action _ %s _ unknown."%(cmd))
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self.log.info("TelldusException : "+error)

    def telldus_reload_config_cb(self):
        """
        Callback for telldus reload config
        @param message : xpl message
        """
        self.log.debug("Telldus reload config received")
        self._mytelldus.reload_config()

    def send_xpl(self, message):
        """
        Callback for sending xpl
        @param add : address of the module
        @param order : the order sent to the unit
        """
        self.log.debug("Telldus send_xpl")
        self.myxpl.send(message)

if __name__ == "__main__":
    Telldus()
