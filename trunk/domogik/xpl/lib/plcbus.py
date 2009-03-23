#!/usr/bin/env python
# -*- encoding:utf-8 -*-

# Copyright 2009 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Authors: François PINET <domopyx@gmail.com>, Yoann HINARD <yoann.hinard@gmail.com>

# $LastChangedBy:$
# $LastChangedDate:$
# $LastChangedRevision:$

import sys, serial

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
    def __init__(self,serial_port_no):


        self._housecodes = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
        self._codevalue = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4, 'F':5, 'G':6, 'H':7, 'I':8, 'J':9, 'K':10, 'L':11, 'M':12, 'N':13, 'O':14, 'P':15}
        self._valuecode=dict()
        for k, v in self._codevalue.items():
            self._valuecode[v]=k
        self._unitcodes = [ i+1 for i in range(16) ]
        self._usercodes = ["0","1","2","3","4","5","6","7","8","9","A","B","C","D","E","F"]
        self._cmdplcbus = {
            'ALL_UNITS_OFF':         '00',#020645000800000c03 because the remote send all user unit off
            'ALL_LIGHTS_ON':         '01',
            'ON':                    '22',#ON and ask to send ACK (instead of '02')
            'OFF':                   '23',#OFF and send ACK
            'DIM':                   '04',
            'BRIGHT':                '05',
            'ALL_LIGHTS_OFF':        '06',
            'ALL_USER_LTS_ON':       '07',
            'ALL_USER_UNIT_OFF':     '08',
            'ALL_USER_LIGHT_OFF':    '09',
            'BLINK':                 '0a',
            'FADE_STOP':             '0b',
            'PRESET_DIM':            '0c',
            'STATUS_OFF':            '0e',
            'STATUS_REQUEST':        '0f',
            'REC_MASTER_ADD_SETUP':  '10',
            'TRA_MASTER_ADD_SETUP':  '11',
            'SCENE_ADR_SETUP':       '12',
            'SCENE_ADR_ERASE':       '13',
            'ALL_SCENES_ADD_ERASE':  '14',
            'FOR FUTURE':            '15',
            'FOR FUTURE':            '16',
            'FOR FUTURE':            '17',
            'GET_SIGNAL_STRENGTH':   '18',
            'GET_NOISE_STRENGTH':    '19',
            'REPORT_SIGNAL_STREN':   '1a',
            'REPORT_NOISE_STREN':    '1b',
            'GET_ALL_ID_PULSE':      '1c',
            'GET_ALL_ON_ID_PULSE':   '1d',
            'REPORT_ALL_ID_PULSE':   '1e',
            'REPORT_ONLY_ON_PULSE':  '1f'}
        #instead of using serial directly, use serialHandler
        self._ser_handler = serialHandler(serial_port_no)
        self._ser_handler.start() #run the handler thread	

    def _valid_item(self, item):
        '''
        Check an item to have good 'HU' syntax
        Raise exception if it is not
        '''
        try:
            if ( item[0].upper() not in self._housecodes ) or ( int(item[1]) not in self._unitcodes ):
                self._log.warning("Invalid item %s%s, must be 'HU'" % (item[0].upper(),item[1]))
        except:
            self._log.warning("Invalid item %s%s, must be 'HU'" % (item[0].upper(),item[1]))
    
    def _valid_house(self, house):
        '''
        Check an house to have good 'H' syntax
        Raise exception if it is not
        '''
        try:
            if house[0] not in self._housecodes:
                self._log.warning("Invalid house %s, must be 'H' format, between A and P" % (house[0].upper()))
        except:
            self._log.warning("Invalid house %s, must be 'H' format, between A and P" % (house[0].upper()))
    
    def _valid_usercode(self, item):
        '''
        Check an user code to have good 'H' syntax
        Raise exception if it is not
        '''
        try:
            if ( item[0].upper() not in self._usercodes ) or ( int(item[1]) not in self._usercodes ):
                self._log.warning("Invalid user code %s, must be 'H' format, between 00 and FF" % (item[0].upper()))
        except:
            self._log.warning("Invalid user code %s, must be 'H' format, between 00 and FF" % (item[0].upper()))
    
        
    def _convert_device_to_hex(self,item):
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
    
    def _send(self, cmd, item, ucod, data1, data2):    #after cmd add level, rate : put in data1 and data2 (just data1 for these cases
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
            print "PLCBUS Frame generation error, command does not exist ",cmd
        else:
            plcbus_frame = '0205%s%s%s%s%s03' % (ucod, self._convert_device_to_hex(item), self._cmdplcbus[cmd], self._convert_data(data1), self._convert_data(data2))   # for bright and dim cmd , call _send with something in data1 and data2 
            print plcbus_frame
            try:
                message=plcbus_frame.decode('HEX')
            except TypeError:
                print "PLCBUS Frame generation error, does not result in a HEX string ",plcbus_frame
            else:
        #exept 
                print "putting in send queue ",plcbus_frame 
                self._ser_handler.add_to_send_queue(plcbus_frame)
            
    def get_all_on_id(self,usercode,housecode):
        '''
        Fastpoll the housecode and return every on modules
        @param usercode : User code of item (must be 'H' syntax between 00 to FF)
        @param housecode : one or more housecodes
        '''
        onlist=[]
        self._send("GET_ALL_ON_ID_PULSE",housecode+"1",usercode)
        response=self._ser_handler.get_from_answer_queue()
        if(response):
            print "Hoora response received ",response
            data=int(response[10:14],16)
            for i in range(0,16):
               if data>>i&1:
                   onlist.append(housecode+str(self._unitcodes[i]))
        print "on :",onlist
        return onlist 
#test
#a=PLCBUSAPI(0)
#a._send("ON","O3","45")
#a._send("BRIGHT","O3,"45","50","1")

# TODO : def close serial port on error
# ser.close()
