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

Get informations about one wire network

Implements
==========

class OneWireException(Exception)
class ComponentDs18b20
class ComponentDs18s20
class ComponentDs2401
class ComponentDs2438
class OneWireNetwork

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ow
import time
import traceback
from threading import Event




class OneWireException(Exception):
    """
    OneWire exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)




class ComponentDs18b20:
    """
    DS18B20 support
    """

    def __init__(self, log, onewire, interval, resolution, callback, stop):
        """
        Return temperature each <interval> seconds
        @param log : log instance
        @param onewire : onewire network object
        @param interval : interval between each data sent
        @param resolution : resolution of data to read
        @param callback : callback to return values
        @param stop : threading.Event instance
        """
        self._log = log
        self.onewire = onewire
        self.interval = interval
        self.resolution = resolution
        self.callback = callback
        self.root = self.onewire.get_root()
        self.old_temp = {}
        self._stop = stop
        self.start_listening()

    def start_listening(self):
        """ 
        Start listening for onewire ds18b20
        """
        while not self._stop.isSet():
            for comp in self.root.find(type = "DS18B20"):
                my_id = comp.id
                try:
                    temperature = float(eval("comp.temperature"+self.resolution))
                except AttributeError:
                    error = "DS18B20 : bad resolution : %s. Setting resolution to 12 for next iterations." % self.resolution
                    self._log.error(error)
                    print(error)
                    self.resolution = "12"

                else:

                    if my_id in self.old_temp:
                        if temperature != self.old_temp[my_id]:
                            my_type = "xpl-trig"
                        else:
                            my_type = "xpl-stat"
                    else:
                        my_type = "xpl-trig"
                    self.old_temp[my_id] = temperature
                    print("type=%s, id=%s, temp=%s" % (my_type, my_id, temperature))
                    self.callback(my_type, {"device" : my_id,
                                         "type" : "temp",
                                         "current" : temperature})
            self._stop.wait(self.interval)

class ComponentDs18s20:
    """
    DS18S20 support
    """

    def __init__(self, log, onewire, interval, callback, stop):
        """
        Return temperature each <interval> seconds
        @param log : log instance
        @param onewire : onewire network object
        @param interval : interval between each data sent
        @param callback : callback to return values
        """
        self._log = log
        self.onewire = onewire
        self.interval = interval
        self.callback = callback
        self.root = self.onewire.get_root()
        self.old_temp = {}
        self.resolution = 12
        self._stop = stop
        self.start_listening()

    def start_listening(self):
        """ 
        Start listening for onewire ds18s20
        """
        while not self._stop.isSet():
            for comp in self.root.find(type = "DS18S20"):
                my_id = comp.id
                try:
                    temperature = float(comp.temperature)
                except AttributeError:
                    error = "DS18S20 : error while reading value"
                    self._log.error(error)
                    print(error)
                    self.resolution = "12"

                else:

                    if my_id in self.old_temp:
                        if temperature != self.old_temp[my_id]:
                            my_type = "xpl-trig"
                        else:
                            my_type = "xpl-stat"
                    else:
                        my_type = "xpl-trig"
                    self.old_temp[my_id] = temperature
                    print("type=%s, id=%s, temp=%s" % (my_type, my_id, temperature))
                    self.callback(my_type, {"device" : my_id,
                                         "type" : "temp",
                                         "current" : temperature})
            self._stop.wait(self.interval)


class ComponentDs2401:
    """
    DS2401 support
    """

    def __init__(self, log, onewire, interval, callback, stop):
        """
        Check component presence each <interval> seconds
        @param log : log instance
        @param onewire : onewire network object
        @param interval : interval between each data sent
        @param callback : callback to return values
        """
        self._log = log
        self.onewire = onewire
        self.interval = interval
        self.callback = callback
        self.root = self.onewire.get_root()
        self.all_ds2401 = {}
        self._stop = stop
        self.start_listening()

    def start_listening(self):
        """ 
        Start listening for onewire ds2401
        """
        while not self._stop.isSet():
            actual_ds2401 = {}
            for comp in self.root.find(type = "DS2401"):
                my_id = comp.id
      
                if my_id in self.all_ds2401:
                    actual_ds2401[my_id] = "HIGH"
                    if self.all_ds2401[my_id] != "HIGH":
                        print("id=%s, status=HIGH" % my_id)
                        self.all_ds2401[my_id] = "HIGH"
                        self.callback("xpl-trig", {"device" : my_id,
                                             "type" : "input",
                                             "current" : "HIGH"})
                else:
                    print("id=%s, status=HIGH" % my_id)
                    self.all_ds2401[my_id] = "HIGH"
                    actual_ds2401[my_id] = "HIGH"
                    self.callback("xpl-trig", {"device" : my_id,
                                         "type" : "input",
                                         "current" : "HIGH"})

            for comp_id in self.all_ds2401:
                if comp_id not in actual_ds2401 and self.all_ds2401[comp_id] == "HIGH":
                    print("id=%s, status=LOW component disappeared)" % (comp_id))
                    self.all_ds2401[my_id] = "LOW"
                    self.callback("xpl-trig", {"device" : comp_id,
                                         "type" : "input",
                                         "current" : "LOW"})
                    
            self._stop.wait(self.interval)
 
    
class ComponentDs2438:
    """
    DS2438 support
    """

    def __init__(self, log, onewire, interval, callback, stop):
        """
        Return temperature each <interval> seconds
        @param log : log instance
        @param onewire : onewire network object
        @param interval : interval between each data sent
        @param callback : callback to return values
        """
        self._log = log
        self.onewire = onewire
        self.interval = interval
        self.callback = callback
        self.root = self.onewire.get_root()
        self.old_temp = {}
        self.old_humidity = {}
        self._stop = stop
        self.start_listening()

    def start_listening(self):
        """ 
        Start listening for onewire ds2438
        """
        while not self._stop.isSet():
            for comp in self.root.find(type = "DS2438"):
                my_id = comp.id
                try:
                    temperature = float(comp.temperature)
                    humidity = float(comp.humidity)
                    print("T=%s" % temperature)
                    print("H=%s" % humidity)
                except AttributeError:
                    error = "DS2438 : error while reading value"
                    self._log.error(error)
                    print(error)

                else:

                    # temperature
                    if my_id in self.old_temp:
                        if temperature != self.old_temp[my_id]:
                            my_type = "xpl-trig"
                        else:
                            my_type = "xpl-stat"
                    else:
                        my_type = "xpl-trig"
                    self.old_temp[my_id] = temperature
                    print("type=%s, id=%s, temp=%s" % (my_type, my_id, temperature))
                    self.callback(my_type, {"device" : my_id,
                                         "type" : "temp",
                                         "current" : temperature})

                    # humidity
                    if my_id in self.old_humidity:
                        if humidity != self.old_humidity[my_id]:
                            my_type = "xpl-trig"
                        else:
                            my_type = "xpl-stat"
                    else:
                        my_type = "xpl-trig"
                    self.old_humidity[my_id] = humidity
                    print("type=%s, id=%s, humidity=%s" % (my_type, my_id, humidity))
                    self.callback(my_type, {"device" : my_id,
                                         "type" : "humidity",
                                         "current" : humidity})
            self._stop.wait(self.interval)



class OneWireNetwork:
    """
    Get informations about 1wire network
    """

    def __init__(self, log, dev = 'u', cache = False):
        """
        Create OneWire instance, allowing to use OneWire Network
        @param dev : device where the interface is connected to,
        default 'u' for USB
        """
        self._log = log
        self._log.info("OWFS version : %s" % ow.__version__)
        try:
            ow.init(dev)
            self._cache = cache
            if cache == True:
                self._root = ow.Sensor('/')
            else:
                self._root = ow.Sensor('/uncached')
        except:
            raise OneWireException("Access to onewire device is not possible. Does your user have the good permissions ? If so, check that you stopped onewire module and you don't have OWFS mounted : %s" % traceback.format_exc())

    def get_root(self):
        """
        Getter for self._root
        """
        return self._root 

