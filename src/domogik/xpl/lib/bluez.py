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
Bluetooth detection.

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
from domogik.xpl.common.xplmessage import XplMessage
import bluetooth
import datetime
import threading
#import logging
#logging.basicConfig()

STATES = ["started", "stopped", "unknown"]
HIGH = "high"
LOW = "low"

class BluezAPI:
    """
    bluez API
    """

    def __init__(self, log, config, myxpl, stop):
        """
        Constructor
        @param plugin : the parent plugin (used to retrieve)
        """
        self.log = log
        self.myxpl = myxpl
        self._config = config
        self._stop = stop
        self._scan_delay = 3
        self._error_delay = 20
        self.listen_adaptator = self._listen_adaptator_lookup
        self._hysteresis = 3
        self._state = "stopped"
        self._device_name = "bluez"
        self._thread = None
        self._targets = dict()

    def reload_config(self):
        """
        """
        self.log.debug("reload_config : Try to get configuration from XPL")
        try:
            self._scan_delay = int(self._config.query('bluez', 'scan-delay'))
            self._error_delay = int(self._config.query('bluez', 'error-delay'))
            self._device_name = str(self._config.query('bluez', 'device-name'))
            listen = str(self._config.query('bluez', 'listen-method'))
            methods = {
            'lookup': lambda : self._listen_adaptator_lookup(),
            'discovery': lambda : self._listen_adaptator_discovery(),
            }
            self.listen_adaptator = methods[listen]
            num = 1
            loop = True
            self._targets = dict()
            while loop == True:
                addr = self._config.query('bluez', \
                    'bt-addr-%s' % str(num))
                name = self._config.query('bluez', \
                    'bt-name-%s' % str(num))
                if addr != None:
                    self._targets[addr] = {"name":name, "count":0, "status":LOW}
                else:
                    loop = False
                num += 1
        except:
            error = "Can't get configuration from XPL : %s" %  \
                     (traceback.format_exc())
            self.log.error("reload_config : " + error)
        #self.log.debug("reload_config : _target=%s" % self._targets)
        self.log.debug("reload_config : Done")

    def start_adaptator(self):
        """
        Start the thread adaptator
        """
        self.log.debug("start_adaptator : Start ...")
        if self._state != "started":
            self._state = "started"
            self.reload_config()
            self._thread = threading.Thread(None,
                                            self.listen_adaptator,
                                            "listen_adaptator",
                                            (),
                                            {})
            self._thread.start()
        self.log.debug("start_adaptator : Done :)")

    def stop_adaptator(self):
        """
        Stop the thread adaptator
        """
        self.log.debug("stop_adaptator : Start ...")
        if self._state != "stopped":
            self._state = "stopped"
            self._thread = None
        self.log.debug("stop_adaptator : Done :)")

    def _listen_adaptator_discovery(self):
        """
        Listen to bluetooth adaptator
        """
        self.log.debug("listen_adaptator : Start ...")
        while not self._stop.isSet() and self._state == "started":
            try:
                self.log.debug("listen_adaptator : Start \
bluetooth.discover_devices at %s" % datetime.datetime.today())
                nearby_devices = bluetooth.discover_devices()
                self.log.debug("listen_adaptator : Stop \
bluetooth.discover_devices at %s" % datetime.datetime.today())
                for aaddr in self._targets:
                    if self._targets[aaddr]["status"] == HIGH :
                        if aaddr not in nearby_devices:
                            self._targets[aaddr]["count"] = \
                                self._targets[aaddr]["count"] +1
                            if self._targets[aaddr]["count"] >= \
                                self._hysteresis:
                                self._trig_detect("xpl-trig", aaddr, LOW)
                                self._targets[aaddr]["status"] = LOW
                for bdaddr in nearby_devices:
                    target_name = bluetooth.lookup_name( bdaddr )
                    if bdaddr in self._targets:
                        self._targets[bdaddr]["count"] = 0
                        if self._targets[bdaddr]["status"] == LOW:
                            self._trig_detect("xpl-trig", bdaddr, HIGH)
                            self._targets[bdaddr]["status"] = HIGH
                            self.log.info("Match bluetooth device %s with \
address %s" % (target_name, bdaddr))
            except:
                self.log.error("listen_adaptator : Can't find bluetooth \
adaptator")
                error = "traceback : %s" %  \
                     (traceback.format_exc())
                self.log.error("listen_adaptator : " + error)
                self._stop.wait(self._error_delay)
            self._stop.wait(self._scan_delay)
        self.log.debug("listen_adaptator : Done :)")

    def _listen_adaptator_lookup(self):
        """
        Listen to bluetooth adaptator
        """
        self.log.debug("listen_adaptator : Start ...")
        while not self._stop.isSet() and self._state == "started":
            try:
                for aaddr in self._targets:
                    self.log.debug("listen_adaptator : Start \
bluetooth.lookup_name at %s" % datetime.datetime.today())
                    target_name = bluetooth.lookup_name( aaddr )
                    self.log.debug("listen_adaptator : Stop \
bluetooth.lookup_name at %s" % datetime.datetime.today())
                    self.log.debug("listen_adaptator : target_name = %s|%s" \
                        % (target_name, aaddr))
                    if target_name == None:
                        if self._targets[aaddr]["status"] == HIGH :
                            self._targets[aaddr]["count"] = \
                                self._targets[aaddr]["count"] +1
                            if self._targets[aaddr]["count"] >= \
                                self._hysteresis:
                                self._trig_detect("xpl-trig", aaddr, LOW)
                                self._targets[aaddr]["status"] = LOW
                                self.log.info("bluetooth device %s with \
address %s is gone" % (target_name, aaddr))
                    else:
                        self._targets[aaddr]["count"] = 0
                        if self._targets[aaddr]["status"] == LOW:
                            self._trig_detect("xpl-trig", aaddr, HIGH)
                            self._targets[aaddr]["status"] = HIGH
                            self.log.info("Match bluetooth device %s with \
address %s" % (target_name, aaddr))
            except:
                self.log.error("listen_adaptator : Can't find bluetooth \
adaptator")
                error = "traceback : %s" %  \
                     (traceback.format_exc())
                self.log.error("listen_adaptator : " + error)
                self._stop.wait(self._error_delay)
            self._stop.wait(self._scan_delay)
        self.log.debug("listen_adaptator : Done :)")

    def basic_listener(self, message):
        """
        Listen to bluez.basic messages
        @param message : The XPL message
        @param myxpl : The XPL sender

        bluez.basic
           {
            action=start|stop|status
            device=<name of the bluez plugin "instance">
            ...
           }
        """
        self.log.debug("basic_listener : Start ...")
        actions = {
            'stop': lambda x, d, m: self._action_stop(x, d),
            'start': lambda x, d, m: self._action_start(x, d),
            'status': lambda x, d, m: self._action_status(x, d),
        }
        device = None
        if 'device' in message.data:
            device = message.data['device']
        try:
            action = None
            if 'action' in message.data:
                action = message.data['action']
            self.log.debug("basic_listener : action %s received \
with device %s" % (action, device))
            actions[action](self.myxpl, device, message)
        except:
            self.log.error("action _ %s _ unknown." % (action))
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self.log.debug("basic_listener : "+error)

    def _action_status(self, myxpl, device):
        """
        Status of the bluez plugin
        timer.basic
           {
            action=status
            ...
           }
        """
        self.log.debug("action_status : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("bluez.basic")
        if device == None:
            mess.add_data({"device" : "unknown"})
        else:
            mess.add_data({"device" : device})
        if device == None and device != self._device_name :
            mess.add_data({"error" : "Unknown device"})
        else:
            mess.add_data({"status" : self._state})
            mess.add_data({"adaptator" : "on"})
        myxpl.send(mess)
        self.log.debug("action_status : Done :)")

    def _action_stop(self, myxpl, device):
        """
        Stop the bluetooth detection
        @param device : The timer to stop
        """
        self.log.debug("_action_stop : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("bluez.basic")
        if device == None:
            mess.add_data({"device" : "unknown"})
        else:
            mess.add_data({"device" : device})
        if device == None and device != self._device_name :
            mess.add_data({"error" : "Unknown device"})
        else:
            self.stop_adaptator()
            mess.add_data({"status" : self._state})
        myxpl.send(mess)
        self.log.debug("_action_stop : Done :)")

    def _action_start(self, myxpl, device):
        """
        Start the bluetooth detection
        @param device : The timer to resume
        """
        self.log.debug("_action_start : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("bluez.basic")
        if device == None:
            mess.add_data({"device" : "unknown"})
        else:
            mess.add_data({"device" : device})
        if device == None and device != self._device_name :
            mess.add_data({"error" : "Unknown device"})
        else:
            self.start_adaptator()
            mess.add_data({"status" : self._state})
        myxpl.send(mess)
        self.log.debug("_action_start : Done :)")

    def _trig_detect(self, xpltype, addr, status):
        """
        """
        self.log.debug("_trig_detect : Start ...")
        mess = XplMessage()
        mess.set_type(xpltype)
        mess.set_schema("sensor.basic")
        mess.add_data({"bluez" : self._device_name})
        mess.add_data({"device" : self._targets[addr]["name"]})
        mess.add_data({"type" :  "ping"})
        mess.add_data({"current" : status})
        self.myxpl.send(mess)
        self.log.debug("_trig_detect : Done :)")

