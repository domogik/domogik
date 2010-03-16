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

Module purpose
==============

Wake on lan client

Implements
==========

- WOLListener

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.module import xPLModule
from domogik.xpl.lib.wol import WOL

IS_DOMOGIK_MODULE = True
DOMOGIK_MODULE_DESCRIPTION = "Wake on lan"
DOMOGIK_MODULE_CONFIGURATION = [
      {"id" : 0,
       "key" : "startup-module",
       "description" : "Automatically start module at Domogik startup",
       "default" : "False"}]


class WOLListener(xPLModule):
    """ Implements a listener for wol messages on xPL network
    """

    def __init__(self):
        """ Create lister for wake on lan
        """
        xPLModule.__init__(self, name = 'wol')
        # Create logger
        self._log.debug("Listener for wake on lan created")
        # Create WOL object
        self._wolmanager = WOL()
        # Create listeners
        Listener(self.wol_cb, self._myxpl, {'schema': 'control.basic',
                'xpltype': 'xpl-cmnd'})

    def wol_cb(self, message):
        """ Call wake on lan lib
            @param message : xPL message detected by listener
        """
        self._log.debug("Call wol_cb")
        if 'device' in message.data:
            device = message.data['device']
        if 'type' in message.data:
            xpl_type = message.data['type']
        if 'current' in message.data:
            current = message.data['current']
        mac = current
        port = 7
        # if it is a wol message for computer
        if device == "computer" and xpl_type == "wakeonlan":
            self._log.debug("Wake on lan command received for " + mac)
            self._wolmanager.wake_up(mac, port)


if __name__ == "__main__":
    WOLL = WOLListener()

