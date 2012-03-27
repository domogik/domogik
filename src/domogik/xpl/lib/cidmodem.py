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

Caller ID with modem support 

Implements
==========

TODO


@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import serial
import re
import traceback



CID_COMMAND = "AT#CID=1"
NUM_START_LINE = "NMBR"
NUM_PATTERN = "NMBR *= *"


class CallerIdModemException(Exception):
    """
    OneWire exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)



class CallerIdModem:
    """ Look for incoming calls with a modem
    """

    def __init__(self, log, callback):
        """ Create handler
        @param device : The full path or number of the device where 
                             modem is connected
        @param callback : method to call each time all data are collected
        """
        self._log = log
        self._cb = callback 


    def open(self, device, cid_command = CID_COMMAND):
        """ open Modem device
        """
        self._log.info("Opening modem device : %s" % device)
        try:
            self._ser = serial.Serial(device, 19200, 
                                      timeout=1)
            self._log.info("Modem opened")
            # Configure caller id mode
            self._log.info("Set modem to caller id mode : %s" % cid_command)
            self._ser.write("%s\r\n" % cid_command)
        except:
            error = "Error while opening modem device : %s : %s" % (device, str(traceback.format_exc()))
            raise CallerIdModemException(error)

    def close(self):
        """ close Modem device
        """
        self._log.info("Close modem device")
        try:
            self._ser.close()
        except:
            error = "Error while closing modem device"
            raise CallerIdModemException(error)

    def listen(self):
        """ listen modem for incoming calls
        """
        self._log.info("Start listening modem")
        while True:
            resp = self.read()
            if resp != None:
                self._cb(resp)



    def read(self):
        """ read one line on modem
        """
        resp = self._ser.readline()
        if NUM_START_LINE in resp:
            # we get the third string's item (separator : blank)
            num = re.sub(NUM_PATTERN, "", resp).strip()
            self._log.debug("Incoming call from '%s'" % num)
            return num
        else:
            return None


