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

Support PLCBUS power-based technology

Implements
==========

- PLCBUSException:.def __init__(self, value):
- PLCBUSException:.def __str__(self):
- PLCBUSAPI:.def __init__(self, serial_port_no):
- PLCBUSAPI:.def _valid_item(self, item):
- PLCBUSAPI:.def _valid_house(self, house):
- PLCBUSAPI:.def _valid_usercode(self, item):
- PLCBUSAPI:.def _convert_device_to_hex(self, item):
- PLCBUSAPI:.def _convert_data(self, data):
- PLCBUSAPI:.def _send(self, cmd, item, ucod, data1, data2):
- PLCBUSAPI:.def get_all_on_id(self, usercode, housecode):

@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
import serial

from struct import *
from time import localtime, strftime
from domogik.common import logger
from domogik.xpl.lib.PLCBusSerialHandler import *


class PLCBUSException:
    '''
    PLCBUS Exception
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.repr(self.value)


class PLCBUSAPI:
    '''
    This class define some facilities to use PLCBUS.
    ALL_USER_UNIT_OFF must be with home unit=00.
    '''

    def __init__(self, serial_port_no):
        self._housecodes = list('ABCDEFGHIJKLMNOP')
        self._valuecode = enumerate(self._housecodes)
        self._codevalue = dict([(v, k) for (k, v) in self._valuecode])
        self._unitcodes = range(1, 17)
        self._usercodes = list('0123456789ABCDEF')
        self._cmdplcbus = {
            #020645000800000c03 because the remote send all user unit off
            'ALL_UNITS_OFF': '00',
            'ALL_LIGHTS_ON': '01',
            'ON': '22', #ON and ask to send ACK (instead of '02')
            'OFF': '23', #OFF and send ACK
            'DIM': '24',
            'BRIGHT': '25',
            'ALL_LIGHTS_OFF': '06',
            'ALL_USER_LTS_ON': '07',
            'ALL_USER_UNIT_OFF': '08',
            'ALL_USER_LIGHT_OFF': '09',
            'BLINK': '0a',
            'FADE_STOP': '0b',
            'PRESET_DIM': '0c',
            'STATUS_ON': '0d',
            'STATUS_OFF': '0e',
            'STATUS_REQUEST': '0f',
            'REC_MASTER_ADD_SETUP': '10',
            'TRA_MASTER_ADD_SETUP': '11',
            'SCENE_ADR_SETUP': '12',
            'SCENE_ADR_ERASE': '13',
            'ALL_SCENES_ADD_ERASE': '14',
            'FOR FUTURE': '15',
            'FOR FUTURE': '16',
            'FOR FUTURE': '17',
            'GET_SIGNAL_STRENGTH': '18',
            'GET_NOISE_STRENGTH': '19',
            'REPORT_SIGNAL_STREN': '1a',
            'REPORT_NOISE_STREN': '1b',
            'GET_ALL_ID_PULSE': '1c',
            'GET_ALL_ON_ID_PULSE': '1d',
            'REPORT_ALL_ID_PULSE': '1e',
            'REPORT_ONLY_ON_PULSE': '1f'}
        #instead of using serial directly, use serialHandler
        self._ser_handler = serialHandler(serial_port_no)
#        self._ser_handler.start() #run the handler thread

    # FIXME: repetition in the following three methods
    # FIXME: the methods don't raise an exception as stated by the docstring

    def _valid_item(self, item):
        '''
        Check an item to have good 'HU' syntax
        Raise exception if it is not
        '''
        h, u = (item[0].upper(), item[1])
        try:
            if not (h in self._housecodes and int(u) in self._unitcodes):
                raise AttributeError
        except:
            self._log.warning("Invalid item %s%s, must be 'HU'" % (h, u))

    def _valid_house(self, house):
        '''
        Check an house to have good 'H' syntax
        Raise exception if it is not
        '''
        try:
            if house[0] not in self._housecodes:
                raise AttributeError
        except:
            self._log.warning("Invalid house %s, must be 'H' format, between "
                    "A and P" % house[0].upper())

    def _valid_usercode(self, item):
        '''
        Check an user code to have good 'H' syntax
        Raise exception if it is not
        '''
        h, u = (item[0].upper(), item[1])
        try:
            if not (h in self._usercodes and int(u) in self._usercodes):
                raise AttributeError
        except:
            self._log.warning("Invalid user code %s, must be 'H' format, "
                    "between 00 and FF" % h)

    def _convert_device_to_hex(self, item):
        var1 = int(item[1:]) - 1
        var2 = '%01X%01x' % (self._codevalue[item[0]], var1)
        return var2

    def _convert_data(self, data):
        # result must have 2 caracters
        var1 = hex(int(data))[2:]
        if len(var1) == 2:
            var2 = '%01X' % (int(data))
            return var2
        else:
            var2 = '0%01X' % (int(data))
            return var2

    def _send(self, cmd, item, ucod, data1 = "00", data2 = "00"):
        # after cmd add level, rate : put in data1 and data2
        # (just data1 for these cases)
        '''
        Send a command PLCBUS to 1141 module
        @param cmd : Command to send ('ON','OFF', etc)
        @param item : Item to send order to (must be "HU" format)
        @param ucod : User code of item (must be 'H' syntax between 00 to FF)
        '''
        # TODO : test on ALL_USER_UNIT_OFF
        #try:
        try:
            command=self._cmdplcbus[cmd]
        except KeyError:
            print "PLCBUS Frame generation error, command does not exist ", cmd
        else:
            if cmd == 'ALL_UNITS_OFF':
                plcbus_frame = '020645000800000c03'
            else:
                plcbus_frame = '0205%s%s%s%s%s03' % (ucod,
                    self._convert_device_to_hex(item), self._cmdplcbus[cmd],
                    self._convert_data(data1), self._convert_data(data2))
            print plcbus_frame
            try:
                message = plcbus_frame.decode('HEX')
            except TypeError:
                print "PLCBUS Frame generation error, does not result in a "\
                        "HEX string ", plcbus_frame
            else:
            #exept
                print "putting in send queue ", plcbus_frame
                self._ser_handler.add_to_send_queue(plcbus_frame)

    def get_all_on_id(self, usercode, housecode):
        '''
        Fastpoll the housecode and return every on modules
        @param usercode : User code of item (must be 'H' syntax between 00 to
        FF)
        @param housecode : one or more housecodes
        '''
        onlist=[]
        self._send("GET_ALL_ON_ID_PULSE", housecode + "1", usercode)
        response=self._ser_handler.get_from_answer_queue()
        if(response):
            print "Hoora response received", response
            data=int(response[10:14], 16)
            for i in range(0, 16):
                if data >> i & 1:
                    onlist.append(housecode + str(self._unitcodes[i]))
        print "on :", onlist
        return onlist

    def stop(self):
        """ Ask thread to stop
        """
        self._ser_handler.stop()

#test
a = PLCBUSAPI("/dev/ttyUSB0")
#a.get_all_on_id("00","B")
print "--------------ON------------------"
a._send("ON", "B2", "00") 
time.sleep(3)
print "--------------STATUS------------------"
a._send("STATUS_REQUEST", "B2", "00") 
time.sleep(3)
print "----------------OFF----------------"
a._send("OFF", "B2", "00") 
time.sleep(3)
#print "---------------STATUS-----------------"
#a._send("STATUS_REQUEST", "B2", "00") 
#time.sleep(3)
#print "---------------BRIGHT-----------------"
#a._send("BRIGHT", "B2", "00", "100","100")
#time.sleep(10)
#print "---------------DIM-----------------"
#a._send("DIM", "B2", "00", "50","0")
#time.sleep(3)
print "---------------STATUS-----------------"
a._send("STATUS_REQUEST", "B2", "00") 
time.sleep(5)
a.stop()

