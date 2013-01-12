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
class BluezAPI

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
from domogik.xpl.common.xplmessage import XplMessage
import bluetooth
import threading
from threading import Timer

#import logging
#logging.basicConfig()

STATES = ["started", "stopped", "unknown"]
HIGH = "high"
LOW = "low"

class BluezAPI:
    """
    bluez API.
    Encapsulate the access to the bluetooth equipment
    """

    def __init__(self, log, config, myxpl, stop):
        """
        Constructor
        @param log : the logger to use
        @param config : the config to use
        @param myxpl : the xpl sender to use
        @param stop : the stop method of the plugin thread

        """
        self.log = log
        self.myxpl = myxpl
        self._config = config
        self._stop = stop
        self._scan_delay = 3
        self._error_delay = 20
        self.delay_sensor = 300
        self.delay_stat = 3
        self.listen_adaptator = self._listen_adaptator_lookup
        self._hysteresis = 3
        self._state = "stopped"
        self._device_name = "bluez"
        self._thread = None
        self._targets = dict()
        self.timer_stat = None

    def reload_config(self):
        """
        Reload config of the plugin.
        """
        self.log.debug("reload_config : Try to get configuration from XPL")
        num = 1
        try:
            self._scan_delay = int(self._config.query('bluez', 'scan-delay'))
            self._error_delay = int(self._config.query('bluez', 'error-delay'))
            self._device_name = str(self._config.query('bluez', 'device-name'))
            self.delay_sensor = int(self._config.query('bluez', 'delay-sensor'))
            self.delay_stat = int(self._config.query('bluez', 'delay-stat'))
            self._hysteresis = int(self._config.query('bluez', 'hysteresis'))

            listen = str(self._config.query('bluez', 'listen-method'))
            methods = {
            'lookup': lambda : self._listen_adaptator_lookup(),
            'discovery': lambda : self._listen_adaptator_discovery(),
            }
            self.listen_adaptator = methods[listen]
            loop = True
            self._targets = dict()
            while loop == True:
                addr = self._config.query('bluez', \
                    'bt-addr-%s' % str(num))
                name = self._config.query('bluez', \
                    'bt-name-%s' % str(num))
                if addr != None:
                    self._targets[addr] = {"name":name, "count":0, "status":LOW}
                    self._trig_detect("xpl-trig", addr, LOW)
                    num += 1
                else:
                    loop = False
            if (self.delay_sensor > 0):
                if self.timer_stat != None:
                    try:
                        self.timer_stat.cancel()
                    except:
                        error = "%s" %  \
                                 (traceback.format_exc())
                        self.log.error("reload_config : " + error)
                self.timer_stat = Timer(self.delay_sensor, self.send_sensors)
                self.timer_stat.start()
        except:
            error = "Can't get configuration from XPL : %s" %  \
                     (traceback.format_exc())
            self.log.error("reload_config : " + error)
        #self.log.debug("reload_config : _target=%s" % self._targets)
        self.log.info("Found %s bluetooth devices in configuration." % (num-1))
        self.log.debug("reload_config : Done")

    def stop_all(self):
        """
        Stop timers and threads.
        """
        self.log.info("stop_all : close all timers and threads.")
        self._state = "stopped"
        if (self.delay_sensor >0):
            self.timer_stat.cancel()

    def send_sensors(self):
        """
        Send the sensors stat messages

        """
        try :
            keys = self._targets.keys()
            for addr in keys :
                wait = False
                if addr in self._targets :
                    status = self._targets[addr]["status"]
                    self._trig_detect("xpl-stat", addr, status)
                if wait :
                    self._stop.wait(self.delay_stat)
                if self._stop.isSet() :
                    break
        except:
            error = "traceback : %s" %  (traceback.format_exc())
            self.log.error("send_sensors : " + error)
        finally :
            self.timer_stat = Timer(self.delay_sensor, self.send_sensors)
            self.timer_stat.start()

    def start_adaptator(self):
        """
        Start the thread listening to the bluetooth adaptator.
        """
        self.log.debug("start_adaptator : Start ...")
        if self._state != "started":
            self.reload_config()
            self._thread = threading.Thread(None,
                                            self._listen_adaptator,
                                            "listen_adaptator",
                                            (),
                                            {})
            self._thread.start()
            self._state = "started"
        self.log.info("Bluetooth detector activated.")
        self.log.debug("start_adaptator : Done :)")

    def stop_adaptator(self):
        """
        Stop the thread listening to the bluetooth adaptator.
        """
        self.log.debug("stop_adaptator : Start ...")
        if self._state != "stopped":
            self.log.info("Bluetooth detector deactivated.")
            self._state = "stopped"
            self._thread = None
            for aaddr in self._targets:
                self._trig_detect("xpl-trig", aaddr, LOW)
        self.log.debug("stop_adaptator : Done :)")

    def _listen_adaptator(self):
        """
        Encapsulate the call to the callback function.
        Catch exception and test thread stop.
        """
        self.log.debug("_listen_adaptator : Start ...")
        while not self._stop.isSet() and self._state == "started":
            try:
                if self.listen_adaptator() == True:
                    self._stop.wait(self._scan_delay)
                else:
                    self.log.debug("_listen_adaptator : Can't listen to adaptator")
                    for aaddr in self._targets:
                        self._trig_detect("xpl-trig", aaddr, LOW)
                    self._stop.wait(self._error_delay)
            except:
                self.log.error("_listen_adaptator : Error when calling listen_method")
                error = "traceback : %s" %  \
                     (traceback.format_exc())
                self.log.error("listen_adaptator : " + error)
                self._stop.wait(self._error_delay)
        self.log.debug("_listen_adaptator : Done :)")

    def _listen_adaptator_discovery(self):
        """
        Listen to bluetooth adaptator. This method use the
        bluetooth.discover_devices(). It takes approcimatively 10 seconds
        to proceed. Phones must be "visible" in bluetooth.
        """
        try:
    #        self.log.debug("_listen_adaptator_discovery : Start \
    #bluetooth.discover_devices at %s" % datetime.datetime.today())
            nearby_devices = bluetooth.discover_devices()
    #        self.log.debug("_listen_adaptator_discovery : Stop \
    #bluetooth.discover_devices at %s" % datetime.datetime.today())
            for aaddr in self._targets:
                if self._targets[aaddr]["status"] == HIGH :
                    if aaddr not in nearby_devices:
                        self._targets[aaddr]["count"] = \
                            self._targets[aaddr]["count"] +1
                        if self._targets[aaddr]["count"] >= self._hysteresis:
                            self._trig_detect("xpl-trig", aaddr, LOW)
            for bdaddr in nearby_devices:
                target_name = bluetooth.lookup_name( bdaddr )
                if bdaddr in self._targets:
                    self._targets[bdaddr]["count"] = 0
                    if self._targets[bdaddr]["status"] == LOW:
                        self._trig_detect("xpl-trig", bdaddr, HIGH)
                        self.log.info("Match bluetooth device %s with address %s" % (target_name, bdaddr))
            return True
        except:
            self.log.error("_listen_adaptator : Error with bluetooth adaptator")
            error = "traceback : %s" %  \
                 (traceback.format_exc())
            self.log.error("listen_adaptator : " + error)
            return False

    def _listen_adaptator_lookup(self):
        """
        Listen to bluetooth adaptator. This method use the
        bluetooth.lookup_name(). It takes approcimatively 3 seconds
        to proceed.
        """
        try:
            for aaddr in self._targets:
    #            self.log.debug("_listen_adaptator_lookup : Start \
    #bluetooth.lookup_name at %s" % datetime.datetime.today())
                target_name = bluetooth.lookup_name( aaddr )
    #            self.log.debug("_listen_adaptator_lookup : Stop \
    #bluetooth.lookup_name at %s" % datetime.datetime.today())
                if target_name == None:
                    if self._targets[aaddr]["status"] == HIGH :
                        self._targets[aaddr]["count"] = \
                            self._targets[aaddr]["count"] +1
                        if self._targets[aaddr]["count"] >= \
                            self._hysteresis:
                            self._trig_detect("xpl-trig", aaddr, LOW)
                            self.log.info("bluetooth device %s with address %s is gone" % (target_name, aaddr))
                else:
                    self._targets[aaddr]["count"] = 0
                    if self._targets[aaddr]["status"] == LOW:
                        self._trig_detect("xpl-trig", aaddr, HIGH)
                        self.log.info("Match bluetooth device %s with address %s" % (target_name, aaddr))
            return True
        except:
            self.log.error("_listen_adaptator : Error with bluetooth adaptator")
            error = "traceback : %s" %  \
                 (traceback.format_exc())
            self.log.error("listen_adaptator : " + error)
            return False

    def basic_listener(self, message):
        """
        Listen to bluez.basic messages.
        @param message : The XPL message received.

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
        if device != None and device == self._device_name:
            try:
                action = None
                if 'action' in message.data:
                    action = message.data['action']
                self.log.debug("basic_listener : action %s received for device %s" % (action, device))
                actions[action](self.myxpl, device, message)
            except:
                self.log.error("action _ %s _ unknown." % (action))
                error = "Exception : %s" %  \
                         (traceback.format_exc())
                self.log.debug("basic_listener : "+error)
        else:
            self.log.warning("basic_listener : action %s received for unknown device %s" % (action, device))

    def _action_status(self, myxpl, device):
        """
        Status of the bluez plugin.
        @param myxpl : The xpl sender to use.
        @param device : The "plugin" device.

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
        mess.add_data({"device" : device})
        mess.add_data({"status" : self._state})
        myxpl.send(mess)
        self.log.debug("action_status : Done :)")

    def _action_stop(self, myxpl, device):
        """
        Stop the bluetooth detection
        @param myxpl : The xpl sender to use.
        @param device : The "plugin" device.
        """
        self.log.debug("_action_stop : Start ...")
        self.stop_adaptator()
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("bluez.basic")
        mess.add_data({"device" : device})
        mess.add_data({"status" : self._state})
        myxpl.send(mess)
        self.log.debug("_action_stop : Done :)")

    def _action_start(self, myxpl, device):
        """
        Start the bluetooth detection
        @param myxpl : The xpl sender to use.
        @param device : The "plugin" device.
        """
        self.log.debug("_action_start : Start ...")
        self.start_adaptator()
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("bluez.basic")
        mess.add_data({"device" : device})
        mess.add_data({"status" : self._state})
        myxpl.send(mess)
        self.log.debug("_action_start : Done :)")

    def _trig_detect(self, xpltype, addr, status):
        """
        Send a message with the status of the "phone" device.
        @param xpltype : The xpltype of the message to send.
        @param addr : the mac address of the bluetooth device.
        @param status : the status of the bluetooth device.
        """
        self.log.debug("_trig_detect : Start ...")
        self._targets[addr]["status"] = status
        mess = XplMessage()
        mess.set_type(xpltype)
        mess.set_schema("sensor.basic")
        mess.add_data({"bluez" : self._device_name})
        mess.add_data({"device" : self._targets[addr]["name"]})
        mess.add_data({"type" :  "ping"})
        mess.add_data({"current" : status})
        self.myxpl.send(mess)
        self.log.debug("_trig_detect : Done :)")

