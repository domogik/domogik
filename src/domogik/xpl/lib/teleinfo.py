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

Téléinfo technology support

Implements
==========

- TeleInfo

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import serial
import threading
import time

class TeleInfo:
    """ Fetch teleinformation datas and call user callback
    each time all data are collected
    """

    def __init__(self, log, serial_port, callback, interval = 60):
        """ @param serial_port : The full path or number of the device where teleinfo is connected
        @param log : log instance
        @param callback : method to call each time all data are collected
        @param interval : seconds to wait between 2 data fetching
        The datas will be passed using a dictionnary
        """
        self._log = log
        self._stop = threading.Event()
        self._thread = self.__TeleInfoHandler(serial_port, callback, float(interval), self._stop, self._log)

    def start(self):
        """ Start the teleinfo handler thread
        """
        self._thread.start()

    def stop(self):
        """ Ask the thread to stop, it can take times
        """
        self._stop.set()


    class __TeleInfoHandler(threading.Thread):
        """ Internal class
        Read data on serial port
        """

        def __init__(self, serial_port, callback, interval, lock, log):
            """ Initialize thread
            """
            threading.Thread.__init__(self)
            self._ser = serial.Serial(serial_port,
                1200, bytesize=7, parity = 'E',stopbits=1)
            self._lock = lock
            self._log = log
            self._interval = interval
            self._cb = callback

        def __del__(self):
            if self._ser.isOpen():
                self._ser.close()

        def run(self):
            """ Start the main loop
            """
            while not self._lock.isSet():
                fr = self._fetch_one_frame()
                self._cb(fr)
                time.sleep(self._interval)

        def _fetch_one_frame(self):
            """ Fetch one full frame for serial port
            If some part of the frame is corrupted,
            it waits until th enext one, so if you have corruption issue,
            this method can take time, but it enures that the frame returned is valid
            @return frame : list of dict {name, value, checksum}
            """
            #Get the begin of the frame, markde by \x02
            fr = self._ser.readline()
            ok = False
            frame = []
            while not ok and not self._lock.isSet():
                try:
                    while '\x02' not in fr:
                        fr = self._ser.readline()
                    #\x02 is in the last line of a frame, so go until the next one
                    fr = self._ser.readline()
                    #A new frame starts
                    #\x03 is the end of the frame
                    while '\x03' not in fr:
                        #Don't use strip() here because the checksum can be ' '
                        if len(fr.replace('\r','').replace('\n','').split()) == 2:
                            #The checksum char is ' '
                            name, value = fr.replace('\r','').replace('\n','').split()
                            checksum = ' '
                        else:
                            name, value, checksum = fr.replace('\r','').replace('\n','').split()
                        if self._is_valid(fr, checksum):
                            frame.append({"name" : name, "value" : value, "checksum" : checksum})
                        else:
                            #This frame is corrupted, we need to wait until the next one
                            frame = []
                            while '\x02' not in fr:
                                fr = self._ser.readline()
                        fr = self._ser.readline()
                    #\x03 has been detected, that's the last line of the frame
                    if len(fr.replace('\r','').replace('\n','').split()) == 2:
                        #The checksum char is ' '
                        name, value = fr.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','').split()
                        checksum = ' '
                    else:
                        name, value, checksum = fr.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','').split()
                    if self._is_valid(fr, checksum):
                        frame.append({"name" : name, "value" : value, "checksum" : checksum})
                        ok = True
                    else:
                        fr = self._ser.readline()
                except ValueError:
                    #Badly formatted frame
                    #This frame is corrupted, we need to wait until the next one
                    frame = []
                    while '\x02' not in fr:
                        fr = self._ser.readline()
            return frame

        def _is_valid(self, frame, checksum):
            """ Check if a frame is valid
            @param frame : the full frame
            @param checksum : the frame checksum
            """
            datas = ' '.join(frame.split()[0:2])
            my_sum = 0
            for c in datas:
                my_sum = my_sum + ord(c)
            computed_checksum = ( sum & int("111111", 2) ) + 0x20
            return chr(computed_checksum) == checksum

###Exemple
def cb( frame):
    """ Print a frame
    """
    for entry in frame :
        print "%s : %s" % (entry["name"], entry["value"])

if __name__ == "__main__":
    tele = TeleInfo('/dev/teleinfo', cb, 5)
    tele.start()
