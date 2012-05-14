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
- PLCBUSAPI:.def send(self, cmd, item, ucod, data1, data2):
- PLCBUSAPI:.def get_all_on_id(self, usercode, housecode):

@author: Domogik project
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik_packages.xpl.lib.PLCBusSerialHandler import serialHandler


class PLCBUSException(Exception):
    '''
    PLCBUS Exception
    '''

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class PLCBUSAPI:
    '''
    This class define some facilities to use PLCBUS.
    ALL_USER_UNIT_OFF must be with home unit=00.
    '''

    def __init__(self, log, serial_port_no, command_cb, message_cb):
        """ Main PLCBus manager
        Use serialHandler for low-level serial management
        @param log : log instance
        @param serial_port_no : Number or path of the serial port
        @param command_cb: callback called when a command has been succesfully sent
        @param message_cb: called when a message is received from somewhere else on the network
        """
        self._log = log
        #For these 2 callbacks, the param is sent as an array
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
            'BLINK': '2a',
            'FADE_STOP': '2b',
            'PRESET_DIM': '2c',
            'STATUS_ON': '0d',
            'STATUS_OFF': '0e',
            'STATUS_REQUEST': '0f',
            'REC_MASTER_ADD_SETUP': '30',
            'TRA_MASTER_ADD_SETUP': '31',
            'SCENE_ADR_SETUP': '12',
            'SCENE_ADR_ERASE': '13',
            'ALL_SCENES_ADD_ERASE': '34',
            #'FOR FUTURE': '15',
            #'FOR FUTURE': '16',
            #'FOR FUTURE': '17',
            'GET_SIGNAL_STRENGTH': '18',
            'GET_NOISE_STRENGTH': '19',
            'REPORT_SIGNAL_STREN': '1a',
            'REPORT_NOISE_STREN': '1b',
            'GET_ALL_ID_PULSE': '1c',
            'GET_ALL_ON_ID_PULSE': '1d',
            'REPORT_ALL_ID_PULSE': '1e',
            'REPORT_ONLY_ON_PULSE': '1f'}
        #instead of using serial directly, use serialHandler
        self._ser_handler = serialHandler(serial_port_no, command_cb, message_cb)
        self._ser_handler.start()

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
            self._log.warning("Invalid house %s, must be 'H' format, between A and P" % house[0].upper())

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
            self._log.warning("Invalid user code %s, must be 'H' format, between 00 and FF" % h)

    def _convert_device_to_hex(self, item):
        if item == None or len(item) == 0:
            return "00"
        elif len(item) == 1:
            return '%01x0' % (self._codevalue[item[0]])
        else: 
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

    def send(self, cmd, item, ucod, data1 = "00", data2 = "00"):
        # after cmd add level, rate : put in data1 and data2
        # (just data1 for these cases)
        '''
        Send a command PLCBUS to 1141 plugin
        @param cmd : Command to send ('ON','OFF', etc)
        @param item : Item to send order to (must be "HU" format)
        @param ucod : User code of item (must be 'H' syntax between 00 to FF)
        '''
        # TODO : test on ALL_USER_UNIT_OFF
        #try:
        try:
            command = self._cmdplcbus[cmd]
        except KeyError:
            print("PLCBUS Frame generation error, command does not exist ", cmd)
        else:
            if cmd == 'ALL_UNITS_OFF':
                plcbus_frame = '020645000800000c03'
            else:
                plcbus_frame = '0205%s%s%s%s%s03' % (ucod,
                    self._convert_device_to_hex(item), self._cmdplcbus[cmd],
                    self._convert_data(data1), self._convert_data(data2))
            try:
                message = plcbus_frame.decode('HEX')
            except TypeError:
                print("PLCBUS Frame generation error, does not result in a HEX string ", plcbus_frame)
            else:
                self._ser_handler.add_to_send_queue(plcbus_frame)

    def get_all_on_id(self, usercode, housecode):
        '''
        Fastpoll the housecode and return every on plugins
        @param usercode : User code of item (must be 'H' syntax between 00 to
        FF)
        @param housecode : one or more housecodes
        '''
        onlist = []
        self.send("GET_ALL_ON_ID_PULSE", housecode + "1", usercode)
#        response = self._ser_handler.get_from_answer_queue()
#        if(response):
#            print "Hoora response received", response
#            data = int(response[10:14], 16)
#            for i in range(0, 16):
#                if data >> i & 1:
#                    onlist.append(housecode + str(self._unitcodes[i]))
#        print "on :", onlist
#        return onlist

    def stop(self):
        """ Ask thread to stop
        """
        self._log.debug("Stopping plcbus serial library")
        self._ser_handler.stop()



##test
#a = PLCBUSAPI("/dev/ttyUSB0")
##a.get_all_on_id("00","B")
#print "--------------ON------------------"
#a.send("ON", "B2", "00")
#time.sleep(3)
#print "--------------STATUS------------------"
#a.send("STATUS_REQUEST", "B2", "00")
#time.sleep(3)
#print "----------------OFF----------------"
#a.send("OFF", "B2", "00")
#time.sleep(3)
#print "---------------STATUS-----------------"
#a.send("STATUS_REQUEST", "B2", "00")
#time.sleep(3)
##print "---------------BRIGHT-----------------"
##a.send("BRIGHT", "B2", "00", "100","100")
##time.sleep(10)
##print "---------------DIM-----------------"
##a.send("DIM", "B2", "00", "50","0")
##time.sleep(3)
#print "---------------STATUS-----------------"
#a.send("STATUS_REQUEST", "B2", "00")
#time.sleep(5)
#a.stop()
#
