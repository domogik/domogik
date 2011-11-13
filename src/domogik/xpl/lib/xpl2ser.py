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

import re
import serial
import traceback
from domogik.xpl.common.xplmessage import REGEXP_TYPE, REGEXP_GLOBAL


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
    __regexp_type = re.compile(REGEXP_TYPE, re.UNICODE | re.VERBOSE)
    __regexp_global = re.compile(REGEXP_GLOBAL, re.DOTALL | re.UNICODE | re.VERBOSE)

    def __init__(self, log, callback, stop):
        """ Create handler

        @param callback : method to call each time all data are collected
        """
        self._log = log
        self._cb = callback 
        self._stop = stop


    def open(self, device, baudrate):
        """ open Serial device

        @param device : The full path or number of the device where 
                             serial is connected
        @param baudrate : speed of serial port (9600, ...)
        """
        self._log.info("Opening serial device : %s" % device)
        try:
            self._ser = serial.Serial(device, baudrate)
            self._log.info("Serial opened")
            print("Serial opened")
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
        print("Start listening serial device")
        current_msg = ""

        # TODO : use a thread issue instead of while True
        while not self._stop.isSet():
            resp = self._ser.readline()
            if self.__regexp_type.match(resp):
                self._log.debug("New start of xpl message detected")
                print("New start of xpl message detected")
                current_msg = resp
            else:
                current_msg += resp
                if self.__regexp_global.match(current_msg):
                    self._cb(current_msg)
                    current_msg = ""


    def write(self,message):
        """ write xpl messages to serial device

        @param message : the xpl message to send to serial device
        """
        self._log.debug("Send xpl message : '%s'" % message)
        print("Send xpl message : '%s'" % message)
        self._ser.write(message)






