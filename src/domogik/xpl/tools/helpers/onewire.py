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

@author: Maxence Dunnewind <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ow


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

    def __init__(self, dev = 'u'):
        """
        Create OneWire instance, allowing to use OneWire Network
        @param dev : device where the interface is connected to,
        default 'u' for USB
        """
        try:
            ow.init(dev)
            self._root_cached = ow.Sensor('/')
            self._root_uncached = ow.Sensor('/uncached')
        except:
            raise OneWireException("Can't access device")
        else:
            self._cache = True
            self._root = self._root_cached
        
        # display all onewire components
        self.show_all_components()
        self.show_ds18b20_detail()
        self.show_ds2401_detail()


    def show_all_components(self):
        print "---- Component list ------------------------------------------"
        for component in self._root.find(all = True):
            print component


    def show_all_attributes(self, component):
        for attr in component.entryList():
            print "   - %s : %s" % (attr, component.__getattr__(attr))


    def show_ds18b20_detail(self):
        print "---- DS18B20 details -----------------------------------------"
        for comp in self._root.find(type = "DS18B20"):
            component = str(comp).split(" - ")[0]
            print "[ %s ]" % component
            print " - Important data"
            print "   - Temperature = %s" % comp.temperature
            print " - All data"
            self.show_all_attributes(comp)


    def show_ds2401_detail(self):
        print "---- DS2401 details ------------------------------------------"
        for comp in self._root.find(type = "DS2401"):
            name = str(comp).split(" - ")[0]
            print "[ %s ]" % name
            print " - Important data"
            print "   - n/a"
            print " - All data"
            self.show_all_attributes(comp)



if __name__ == "__main__":
    my_onewire = OneWireNetwork()
