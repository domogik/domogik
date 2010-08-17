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
import time
import traceback

class TeleinfoException(Exception):
    """
    Teleinfo exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Teleinfo:
    """ Fetch teleinformation datas and call user callback
    each time all data are collected
    """

    def __init__(self, log, callback):
        """ @param device : teleinfo modem device path
        @param log : log instance
        @param callback : method to call each time all data are collected
        The datas will be passed using a dictionnary
        """
        self._log = log
        self._callback = callback
        self._ser = None


    def open(self, device):
        """ open teleinfo modem device
            @param device : teleinfo device path
        """
        try:
            self._log.info("Try to open Teleinfo modem '%s'" % device)
            self._ser = serial.Serial(device, 1200, bytesize=7, 
                                      parity = 'E',stopbits=1)
            self._log.info("Teleinfo modem successfully opened")
        except:
            error = "Error opening Teleinfo modem '%s' : %s" %  \
                     (device, traceback.format_exc())
            raise TeleinfoException(error)

    def close(self):
        """ close telinfo modem
        """
        if self._ser.isOpen():
            self._ser.close()

    def listen(self, interval):
        """ Start the main loop
            @param interval : time between each read
        """
        while True:
            frame = self.read()
            self._log.debug("Frame received : %s" % frame)
            self._callback(frame)
            time.sleep(interval)

    def read(self):
        """ Fetch one full frame for serial port
        If some part of the frame is corrupted,
        it waits until th enext one, so if you have corruption issue,
        this method can take time but it enures that the frame returned is valid
        @return frame : list of dict {name, value, checksum}
        """
        #Get the begin of the frame, markde by \x02
        resp = self._ser.readline()
        is_ok = False
        frame = []
        while not is_ok:
            try:
                while '\x02' not in resp:
                    resp = self._ser.readline()
                #\x02 is in the last line of a frame, so go until the next one
                resp = self._ser.readline()
                #A new frame starts
                #\x03 is the end of the frame
                while '\x03' not in resp:
                    #Don't use strip() here because the checksum can be ' '
                    if len(resp.replace('\r','').replace('\n','').split()) == 2:
                        #The checksum char is ' '
                        name, value = resp.replace('\r','').replace('\n','').split()
                        checksum = ' '
                    else:
                        name, value, checksum = resp.replace('\r','').replace('\n','').split()
                    if self._is_valid(resp, checksum):
                        frame.append({"name" : name, "value" : value, "checksum" : checksum})
                    else:
                        #This frame is corrupted, we need to wait until the next one
                        frame = []
                        while '\x02' not in resp:
                            resp = self._ser.readline()
                    resp = self._ser.readline()
                #\x03 has been detected, that's the last line of the frame
                if len(resp.replace('\r','').replace('\n','').split()) == 2:
                    #The checksum char is ' '
                    name, value = resp.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','').split()
                    checksum = ' '
                else:
                    name, value, checksum = resp.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','').split()
                if self._is_valid(resp, checksum):
                    frame.append({"name" : name, "value" : value, "checksum" : checksum})
                    is_ok = True
                else:
                    resp = self._ser.readline()
            except ValueError:
                #Badly formatted frame
                #This frame is corrupted, we need to wait until the next one
                frame = []
                while '\x02' not in resp:
                    resp = self._ser.readline()
        return frame

    def _is_valid(self, frame, checksum):
        """ Check if a frame is valid
        @param frame : the full frame
        @param checksum : the frame checksum
        """
        datas = ' '.join(frame.split()[0:2])
        my_sum = 0
        for cks in datas:
            my_sum = my_sum + ord(cks)
        computed_checksum = ( my_sum & int("111111", 2) ) + 0x20
        return chr(computed_checksum) == checksum
