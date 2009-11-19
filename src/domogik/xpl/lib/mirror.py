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

Mir:ror (Violet) support

Implements
==========

- Mirror
-   __MirrorHandler

@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import threading 
import binascii
import time
from domogik.common import logger

class Mirror:
    """ Listen to mir:ror 
    """

    def __init__(self, mirrorDevice, nbMaxTry, interval, callback):
        """ @param mirrorDevice : device of mir:ror (/dev/hidrawX)
        @param callback : method to call each time all data are collected
        """
        self._stop = threading.Event()
        self._thread = self.__MirrorHandler(mirrorDevice, int(nbMaxTry), \
                                            float(interval), callback, self._stop)

    def start(self):
        """ Start the mirror handler thread 
        """
        self._thread.start() 

    def stop(self):
        """ Ask the thread to stop, it can take times
        """
        self._stop.set()


    class __MirrorHandler(threading.Thread):
        """ Internal class 
        Read data mir:ror device
        """

        def __init__(self, mirrorDevice, nbMaxTry, interval, callback, lock):

            # logging initialization
            l = logger.Logger('Mirror')
            self._log = l.get_logger()

            self._log.info("mir:ror initialisation...")
            self._lock = lock
            self._cb = callback 
            self._deviceNotOpen = 1
            nbTry = 0
            while self._deviceNotOpen and nbTry < nbMaxTry:
                self._log.debug("- open " + mirrorDevice)
                try:
                    self._mirror = open(mirrorDevice, "rb")
                    self._deviceNotOpen = 0
                    self._log.debug("- mir:ror open")
                except:
                    self._log.error("- error while opening " + mirrorDevice + \
                                    "(" + str(nbTry+1) + "/" + str(nbMaxTry) + "). Next try in 15s")
                    # device is not connected : we wait for 15s before next try
                    time.sleep(interval)
                    nbTry = nbTry + 1

            # Initialize thread 
            threading.Thread.__init__(self)


        def __del__(self):
            if self._mirror.isOpen():
                self._log.debug("Close " + mirrorDevice)
                self._mirror.close()

        def run(self):
            # listen to mir:ror
            if self._deviceNotOpen == 0:
                self._log.info("Start listening mirror")
                while not self._lock.isSet():
                    # We read 16 byte
                    data = self._mirror.read(16)
                    # if the first byte is not null, this is a message
                    if data[0] != '\x00':
                        # first byte : action type : ztamp or action on mir:ror
                        if data[0] == '\x02':
                            ### action on ztamp
                            # data[0] and data[1] : action type
                            # data[2...15] : ztamp identifier (it seems that 2,3, 14,15 are always nulls)
                            self._log.debug("Action on : ztamp")
                            ztampId = binascii.hexlify(data[2]+data[3]+data[4]+data[5]+data[6]+ \
                                             data[7]+data[8]+data[9]+data[10]+ \
                                             data[11]+data[12]+data[13]+data[14]+data[15])
                            if data[1] == '\x01':
                                self._log.debug("ztamp near from mir:ror : "+ztampId)
                                self._cb("ztamp_in", ztampId)
                            if data[1] == '\x02':
                                self._log.debug("ztamp far from mir:ror : "+ztampId)
                                self._cb("ztamp_out", ztampId)

                        if data[0] == '\x01':
                            ### action on mir:ror
                            # Only the data[0] and data[1] are used in this case. The others are nulls
                            self._log.debug("Action on : mir:ror")
                            if data[1] == '\x04':
                                self._log.debug("mir:ror faced up")
                                self._cb("mirror_up", "0")
                            if data[1] == '\x05':
                                self._log.debug("mir:ror faced down")
                                self._cb("mirror_down", "0")
            else:
                self._log.error("No mirror detected")





###Exemple
def cb(action, ztampId):
    print "ACTION : %s" % action
    print "ZTAMPID : %s" % ztampId

if __name__ == "__main__":
    mirror = Mirror('/dev/hidraw0', 15, 10, cb)
    mirror.start()
