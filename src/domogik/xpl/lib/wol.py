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

Wake on lan support

Implements
==========

- WOL._init
- WOL._wol

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import socket
import struct
import threading
from domogik.common import logger
from domogik.common.ordereddict import OrderedDict

class WOL:
    """
    This class allow to use Wake on Lan
    """

    def __init__(self):
        l = logger.Logger('WOL')
        self._log = l.get_logger()

    def _wol(self, mac, port):
        """
        Send a magic packet to wake a computer on lan
        """
        self._log.info("Start process for wol on " + mac + " port:" + str(port))
        # Verify and conveert mac format
        self._log.debug("Check mac format")
        if len(mac) == 12:
            pass
        elif len(mac) == 12 + 5:
            separator = mac[2]
            mac = mac.replace(separator, '')
        else:
            self._log.error("Wrong mac address : " + mac)
            return
     
        # Create magic packet
        self._log.debug("Create magic packet")
        magicPacket = ''.join(['FFFFFFFFFFFF', mac * 20])
        magicHexa = '' 
    
        # Convert magic packet in hexa
        for i in range(0, len(magicPacket), 2):
            magicHexa = ''.join([magicHexa,
                                 struct.pack('B', int(magicPacket[i: i + 2], 16))])
    
        # Send magic packet
        self._log.debug("Send magic packet to broadcast")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magicHexa, ('<broadcast>', port))
            self._log.info("Magic packet send")
        except:
            self._log.error("Fail to send magic packet")
    
