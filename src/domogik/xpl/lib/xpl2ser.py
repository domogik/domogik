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

Xpl bridge between ethernet and serial 

Implements
==========

TODO


@author: Kriss
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import serial
import traceback


START_MESSAGE = "xpl-"


class XplBridgeException(Exception):
    """
    xpl2ser exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)



class XplBridge:
    """ Look for xpl message from serial device
    """

    def __init__(self, log, callback):
        """ Create handler

        @param callback : method to call each time all data are collected
        """
        self._log = log
        self._cb = callback 


    def open(self, device):
        """ open Serial device

        @param device : The full path or number of the device where 
                             serial is connected
        """
        self._log.info("Opening serial device : %s" % device)
        try:
            self._ser = serial.Serial(device, 9600, 8, "O",
                                      timeout=1)
            self._log.info("Serial opened")
        except:
            error = "Error while opening serial device : %s : %s" % (device, str(traceback.format_exc()))
            raise XplBridgeException(error)

    def close(self):
        """ close Serial device
        """
        self._log.info("Close serial device")
        try:
            self._ser.close()
        except:
            error = "Error while closing serial device"
            raise XplBridgeException(error)


    def listen(self):
        """ listen serial for xpl messages
        """
        self._log.info("Start listening serial device")
        while True:
            resp = self.read()
            if resp != None:
                self._cb(resp)

    def read(self):
        """ read xpl messages from serial device
        """
        resp = self._ser.readline()
        if START_MESSAGE in resp:
            self._log.debug("Xpl Message : '%s'" % resp)
            return resp
        else:
            return None


    def write(self,message):
        """ write xpl messages to serial device

        @param message : the xpl message to send to serial device
        """
        self._log.debug("Send xpl message : '%s'" % message)
        self._ser.write(message)






