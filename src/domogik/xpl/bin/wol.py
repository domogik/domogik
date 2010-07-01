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
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.wol import WOL


class WOLListener(XplPlugin):
    """ Implements a listener for wol messages on xPL network
    """

    def __init__(self):
        """ Create lister for wake on lan
        """
        XplPlugin.__init__(self, name = 'wol')
        # Create WOL object
        self._wolmanager = WOL(self._log)
        # Create listeners
        Listener(self.wol_cb, self._myxpl, {'schema': 'control.basic',
                'xpltype': 'xpl-cmnd', 'type': 'wakeonlan', 'current': 'on'})
        self._log.debug("Listener for wake on lan created")

    def wol_cb(self, message):
        """ Call wake on lan lib
            @param message : xPL message detected by listener
        """
        if 'device' in message.data:
            device = message.data['device']
        mac = device
        port = 7
        self._log.info("Wake on lan command received for " + mac)
        status = self._wolmanager.wake_up(mac, port)

        # Send xpl-trig to say plugin receive command
        if status == True:
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('sensor.basic')
            mess.add_data({'device' :  mac})
            mess.add_data({'type' :  'wakeonlan'})
            mess.add_data({'current' :  'on'})
            self._myxpl.send(mess)


if __name__ == "__main__":
    WOLL = WOLListener()

