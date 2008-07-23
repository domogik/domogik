#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2008-07-23 21:42:29 +0200 (mer. 23 juil. 2008) $
# $LastChangedRevision: 100 $

import ow

class OneWireException:
    """
    OneWire exception
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.repr(self.value)

class OneWire:
    """
    Manage OneWire 
    """
    def __init__(self, dev = 'u'):
        """
        Create OneWire instance, allowing to use OneWire Network
        @param dev : device where the interface is connected to, default 'u' for USB
        """
        try:
            ow.init(dev)
            self._root_cached = ow.Sensor( '/' )
            self._root_uncached = ow.Sensor('/uncached')
        except:
            raise OneWireException, "Can't access device"
        else:
            self._cache = True
            self._root = self._root_cached

     
    def set_cache_use(self, use):
        """
        Define use of cache.
        If it's set to False, information will be reactualised each time a request is done
        If it's true, the OWFS cache will be used (from 15s to 2 minutes of cache)
        """
        self._cache = use
        if self._cache:
            self._root = self._root_cached
        else:
            self._root = self._root_uncached
        
    def exec_type(self, t = ''):
        """
        Find all sensors matching a type
        """
        return self._root.find(type = t)

    def exec_name(self, n = ''):
        """
        Find all sensors matching a name
        """
        return self._root.find(name = n)

    def exec_family(self, f = ''):
        """
        Find all sensors matching a family
        """
        return self._root.find(family = f)

    def get_temperature(self):
        """
        Return list of all temperature indicated by DS18B20 and DS18S20 sensors
        @return list of (id, temperature)
        """
        return [ (i.id, i.type, i.temperature.replace(" ","")) for i in self.exec_type(t='DS18S20') ]  + [ (i.id, i.type, i.temperature.replace(" ","")) for i in self.exec_type(t='DS18B20') ]

    def is_present(self, item):
        """
        Check if an item is on the network, and if it is, check if the present property is set to 1
        """
        if item[0] != '/':
            item = '/%s' % item
        try:
            i = exec_name(item)
            return i[0].present
        except:
            return False

