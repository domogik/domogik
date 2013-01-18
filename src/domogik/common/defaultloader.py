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

Load config from /etc/default/domogik file

Implements
==========

- DefaultLoader

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os


CONFIG_FILE = "/etc/default/domogik"

class DefaultLoader():
    '''
    Parse Domogik default file
    '''

    def __init__(self):
        '''
        Load the file in a dict
        '''
        self._cfg = {}
        my_file = open(CONFIG_FILE, 'r')
        for line in my_file:
            if line[0] != "#":
                buf = line.strip().split("=")
                if len(buf) >= 2:
                    self._cfg[buf[0]] = buf[1]

    def get(self, key):
        """ Get the value of a key of the file
            @param key : the ley to get the value
        """
        return self._cfg[key]
