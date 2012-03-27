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

TODO

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ow
from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.common import logger
import traceback

ACCESS_ERROR = "Access to onewire device is not possible. Does your user have the good permissions ? If so, check that you stopped onewire module and you don't have OWFS mounted"

class Onewire(Helper):
    """ Onewire helpers
    """

    def __init__(self):
        """ Init onewire helper
        """

        self.commands =   \
               { "all" : 
                  {
                    "cb" : self.all,
                    "desc" : "Show all devices found on onewire network",
                    "min_args" : 1,
                    "usage" : "all <adaptator device>"
                  },
                  "detail" : 
                  {
                    "cb" : self.detail,
                    "desc" : "Show detail for a device.",
                    "min_args" : 1,
                    "usage" : "detail <adaptator device> <device id>"
                  },
                  "ds18b20" : 
                  {
                    "cb" : self.ds18b20,
                    "desc" : "Show detail for all DS18B20 devices",
                    "min_args" : 1,
                    "usage" : "ds18b20 <adaptator device>"
                  },
                  "ds18s20" : 
                  {
                    "cb" : self.ds18s20,
                    "desc" : "Show detail for all DS18S20 devices",
                    "min_args" : 1,
                    "usage" : "ds18s20 <adaptator device>"
                  },
                  "ds2401" : 
                  {
                    "cb" : self.ds2401,
                    "desc" : "Show detail for all DS2401 devices",
                    "min_args" : 1,
                    "usage" : "ds2401 <adaptator device>"
                  },
                  "ds2438" : 
                  {
                    "cb" : self.ds2438,
                    "desc" : "Show detail for all DS2438 devices",
                    "min_args" : 1,
                    "usage" : "ds2438 <adaptator device>"
                  }
                }

        log = logger.Logger('onewire-helper')
        self._log = log.get_logger('onewire-helper')
        self.my_ow = None

    def all(self, args = None):
        """ show all components
        """
        try:
            self.my_ow = OneWireNetwork(args[0], self._log)
        except OneWireException as err:
            raise HelperError(err.value)
        return self.my_ow.show_all_components()

    def detail(self, args = None):
        """ show one component detail
        """
        try:
            self.my_ow = OneWireNetwork(args[0], self._log)
        except OneWireException as err:
            raise HelperError(err.value)
        return self.my_ow.show_component_detail(args[1])

    def ds18b20(self, args = None):
        """ show ds18b20 components
        """
        try:
            self.my_ow = OneWireNetwork(args[0], self._log)
        except OneWireException as err:
            raise HelperError(err.value)
        return self.my_ow.show_ds18b20_detail()

    def ds18s20(self, args = None):
        """ show ds18s20 components
        """
        try:
            self.my_ow = OneWireNetwork(args[0], self._log)
        except OneWireException as err:
            raise HelperError(err.value)
        return self.my_ow.show_ds18s20_detail()

    def ds2401(self, args = None):
        """ show ds2401 components
        """
        try:
            self.my_ow = OneWireNetwork(args[0], self._log)
        except OneWireException as err:
            raise HelperError(err.value)
        return self.my_ow.show_ds2401_detail()

    def ds2438(self, args = None):
        """ show ds2438 components
        """
        try:
            self.my_ow = OneWireNetwork(args[0], self._log)
        except OneWireException as err:
            raise HelperError(err.value)
        return self.my_ow.show_ds2438_detail()


class OneWireException:
    """
    OneWire exception
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.repr(self.value)


class OneWireNetwork:
    """
    Get informations about 1wire network
    """

    def __init__(self, dev, log):
        """
        Create OneWire instance, allowing to use OneWire Network
        @param dev : device where the interface is connected to,
        default 'u' for USB
        """
        self._log = log
        try:
            ow.init(str(dev))
            self._root_cached = ow.Sensor('/')
            self._root_uncached = ow.Sensor('/uncached')
        except:
            self._log.error("%s : %s : %s" % (dev, ACCESS_ERROR, traceback.format_exc()))
            raise OneWireException("%s. See log file for complete trace" % (ACCESS_ERROR))
        else:
            self._cache = True
            self._root = self._root_cached


    def show_all_components(self):
        """ show all components
        """
        ret = []
        display = "| %-6s | %-12s | %-10s |"
        sep = "--------------------------------------"
        ret.append(display % ("Family", "Component id", "Type"))
        ret.append(sep)
        for comp in self._root.find(all = True):
            ret.append(display % (comp.family, comp.id, comp.type))
        return ret


    def show_component_detail(self, my_id):
        """ show one component detail
        """
        ret = []
        for comp in self._root.find(id = my_id):
            # component detail
            print("C=%s" % comp)
            display = " - %-20s : %s" 
            ret.append("%s attributes :" % my_id)
            for attr in comp.entryList():
                try:
                    print("ATTR=%s" % attr)
                    ret.append(display % (attr, comp.__getattr__(attr)))
                # Patch with owfs 2.8p4 : the 2 following excepts weren't needed
                # with a previous owfs release (2.7 maybe)
                # It would be interesting to comment this to test in following 
                # releases
                except ow.exUnknownSensor:
                    pass
                except AttributeError:
                    pass
        return ret


    def show_ds18b20_detail(self):
        """ show ds18b20 components
        """
        ret = []
        display = " - %-30s : %s"
        for comp in self._root.find(type = "DS18B20"):
            ret.append("DS18B20 : id=%s" % comp.id)
            ret.append(display % ("Temperature", comp.temperature))
            ret.append(display % ("Powered (1) / parasit (0)", comp.power))
        return ret


    def show_ds18s20_detail(self):
        """ show ds18s20 components
        """
        ret = []
        display = " - %-30s : %s"
        for comp in self._root.find(type = "DS18S20"):
            ret.append("DS18S20 : id=%s" % comp.id)
            ret.append(display % ("Temperature", comp.temperature))
            ret.append(display % ("Powered (1) / parasit (0)", comp.power))
        return ret


    def show_ds2401_detail(self):
        """ show ds2401 components
        """
        ret = []
        display = " - %-30s : %s"
        for comp in self._root.find(type = "DS2401"):
            ret.append("DS2401 : id=%s" % comp.id)
            ret.append(display % ("Present", "yes"))
        return ret


    def show_ds2438_detail(self):
        """ show ds2438 components
        """
        ret = []
        display = " - %-30s : %s"
        for comp in self._root.find(type = "DS2438"):
            ret.append("DS2438 : id=%s" % comp.id)
            ret.append(display % ("Temperature", comp.temperature))
            ret.append(display % ("Humidity", comp.humidity))
        return ret


MY_CLASS = {"cb" : Onewire}

