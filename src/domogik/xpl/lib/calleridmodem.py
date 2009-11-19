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

Caller ID with modem support 

Implements
==========

- CallerIdModem
-   __CallerIdModemHandler

@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import serial
import threading 
import time
from domogik.common import logger

class CallerIdModem:
    """ Look for incoming calls with a modem
    """

    def __init__(self, serial_port, nbmaxtry, interval, callback):
        """ @param serial_port : The full path or number of the device where modem is connected
        @param nbmaxtry : number max of tries to open modem
        @param interval : delay between each try to open modem
        @param callback : method to call each time all data are collected
        """
        self._stop = threading.Event()
        self._thread = self.__CallerIdModemHandler(serial_port, int(nbmaxtry), \
                                                   float(interval), callback, self._stop)

    def start(self):
        """ Start the caller id handler thread 
        """
        self._thread.start() 

    def stop(self):
        """ Ask the thread to stop, it can take times
        """
        self._stop.set()


    class __CallerIdModemHandler(threading.Thread):
        """ Internal class 
        Read data on serial port
        """

        def __init__(self, serial_port, nbMaxTry, interval, callback, lock):

            # logging initialization
            l = logger.Logger('CallerIdModem')
            self._log = l.get_logger()

            self._log.debug("cidmodem initialisation...")
            self._lock = lock
            self._cb = callback 
            self._deviceNotOpen = 1
            nbTry = 0
            while self._deviceNotOpen and nbTry < nbMaxTry:
                self._log.debug("- open " + serial_port)
                try:
                    self._ser = serial.Serial(serial_port, 19200, timeout=1)
                    self._deviceNotOpen = 0
                    self._log.debug("- Modem open")
                except:
                    self._log.error("- error while opening " + serial_port + \
                                    "(" + str(nbTry+1) + "/" + str(nbMaxTry) + "). Next try in 15s")
                    # device is not connected : we wait for 15s before next try
                    time.sleep(interval)
                    nbTry = nbTry + 1

            # Initialize thread 
            threading.Thread.__init__(self)


        def __del__(self):
            if self._ser.isOpen():
                self._log.debug("Close " + serial_port)
                self._ser.close()

        def run(self):
            if self._deviceNotOpen == 0:
                self._log.info("Start managing modem")
                # Configure caller id mode
                self._log.debug("Set modem to caller id mode : AT#CID=1")
                self._ser.write("AT#CID=1\r\n")
                # listen to modem
                self._log.debug("Start listening modem")
                while not self._lock.isSet():
                    resp=self._ser.readline()
                    if "NMBR" in resp:
                        # we get the third string's item (separator : blank)
                        f = lambda s,d=' ': s.split(d)[2].strip()
                        self._log.debug("Incoming call from " + f(resp))
                        self._cb(f(resp))
            else:
                self._log.error("No Modem detected")




###Exemple
def cb(data):
    # Print a data 
    print "DATA : %s" % data

if __name__ == "__main__":
    callerid = CallerIdModem('/dev/ttyUSB1', cb)
    callerid.start()
