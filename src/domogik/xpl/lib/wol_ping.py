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

Wake on lan support

Implements
==========

- WOL._init
- WOL.wake_up

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import XplTimer
import socket
import struct
from threading import Thread
import subprocess
import time
import traceback

class WOL:
    """
    This class allow to use Wake on Lan
    """

    def __init__(self, log):
        """
        Init object
        @param log : logger instance
        """
        self._log = log

    def wake_up(self, mac, port):
        """
        Send a magic packet to wake a computer on lan
        """
        self._log.debug("Start processing wol on %s port %s" % (mac, str(port)))
        # Verify and conveert mac format
        self._log.debug("Check mac format")
        if len(mac) == 12:
            pass
        elif len(mac) == 12 + 5:
            separator = mac[2]
            mac = mac.replace(separator, '')
        else:
            self._log.error("Wrong mac address : " + mac)
            return False

        # Create magic packet
        self._log.debug("Create magic packet")
        magic_packet = ''.join(['FFFFFFFFFFFF', mac * 20])
        magic_hexa = ''

        # Convert magic packet in hexa
        for i in range(0, len(magic_packet), 2):
            magic_hexa = ''.join([magic_hexa, 
                         struct.pack('B', int(magic_packet[i: i + 2], 16))])

        # Send magic packet
        self._log.debug("Send magic packet to broadcast")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_hexa, ('<broadcast>', port))
            self._log.info("Magic packet send")
            sock.close()
            return True
        except:
            self._log.error("Fail to send magic packet : %s" % traceback.format_exc())
            return False



class Ping:
    """
    This class allow to ping a computer
    """

    def __init__(self, myxpl, log, cb, interval, computers):
        """
        Init object
        @param log : logger instance
        """
        self.myxpl = myxpl
        self._log = log
        self._cb = cb
        self._interval = interval
        self._computers = computers

    def ping(self):
        """ Ping computers
        """
        self._ping_thr = XplTimer(self._interval, \
                                  self.ping_list,
                                  self.myxpl)
        self._ping_thr.start()

    def ping_list(self):
        """ Ping list of computers
        """
        for computer in self._computers:
            try:
                old_status = self._computers[computer]["old_status"]
            except KeyError:
                # First ping, no old status for ping
                old_status = None
            self._log.debug("Pinging %s (%s)" % (computer, self._computers[computer]["ip"]))
            print("Pinging %s (%s)" % (computer, self._computers[computer]["ip"]))
            ret = subprocess.call("ping -c 1 %s" % self._computers[computer]["ip"],
                            shell=True,
                            stdout=open('/dev/null', 'w'),
                            stderr=subprocess.STDOUT)
            if ret == 0:
                self._log.debug("%s: is alive" % computer)
                print("%s: is alive" % computer)
                status = "high"
            else:
                self._log.debug("%s: did not respond" % computer)
                print("%s: did not respond" % computer)
                status = "low"

            if status != old_status:
                type = "xpl-trig"
            else:
                type = "xpl-stat"
            self._computers[computer]["old_status"] = status
      
            self._cb(type, computer, status)

