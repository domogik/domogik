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

Support One-Wire bus

Implements
==========

- OneWireException:.__init__(self, value)
- OneWireException:.__str__(self)
- OneWire:.__init__(self, dev = 'u')
- OneWire:.set_cache_use(self, use)
- OneWire:.exec_type(self, t = '')
- OneWire:.exec_name(self, n = '')
- OneWire:.exec_family(self, f = '')
- OneWire:.get_temperature(self)
- OneWire:.get_temperatures(t)
- OneWire:.is_present(self, item)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ow


class OneWireException(Exception):
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

    def set_cache_use(self, use):
        """
        Define use of cache.
        If it's set to False, information will be reactualised each time a
        request is done
        If it's true, the OWFS cache will be used (from 15s to 2 minutes of
        cache)
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

    def get_temperatures(self):
        """
        Return list of all temperature indicated by DS18B20 and DS18S20 sensors
        @return list of (id, temperature)
        """
        return self.get_temperature('DS18S20') + self.get_temperature('DS18B20')

    def get_temperature(self, t):
        return [(i.id, i.type, i.temperature.replace(" ", "")) for i in
                self.exec_type(t=t)]

    def is_present(self, item):
        """
        Check if an item is on the network, and if it is, check if the present
        property is set to 1
        """
        if item[0] != '/':
            item = '/%s' % item
        try:
            i = exec_name(item)
            return i[0].present
        except:
            return False
