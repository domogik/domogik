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

Send time informations on the network

Implements
==========

- ModuleSample.__init__(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.plugin import xPLPlugin


###
# Uncomment the next lines to let your plugin be autodetected by the manager
#
#IS_DOMOGIK_PLUGIN = True
#DOMOGIK_PLUGIN_TECHNOLOGY = "RFID, X10, Communication, etc"
#DOMOGIK_PLUGIN_DESCRIPTION = "My short module description"
#DOMOGIK_PLUGIN_CONFIGURATION=[
#      {"id" : 0,
#       "key" : "startup-plugin",
#       "description" : "Automatically start plugin at Domogik startup",
#       "default" : "False"},
#       ]

class PluginSample(xPLPlugin):
    '''
    Module description
    '''

    def __init__(self):
        xPLPlugin.__init__(self, name = 'mdspl')

if __name__ == "__main__":
    PluginSample()
