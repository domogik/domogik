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

# Author: François PINET <domopyx@gmail.com>

# $LastChangedBy:$
# $LastChangedDate:$
# $LastChangedRevision:$

# 02 05 FF B0 22 00 00 03



    # 0  => "Same home: ALL UNITS OFF",
    # 1  => "Same home + unit: ALL LIGHTS ON",
    # 2  => "Same home + unit: UNIT ON",
    # 3  => "Same home + unit: UNIT OFF",
    # 4  => "Same home + unit: UNIT DIM",
    # 5  => "Same home + unit: UNIT BRIGHT",
    # 6  => "Same home: ALL LIGHTS OFF",
    # 7  => "Same user: ALL USER LIGHTS ON",
    # 8  => "Same user: ALL USER UNITS OFF",
    # 9  => "Same user: ALL USER LIGHTS OFF",
    # 10 => "Same home + unit: ONE LIGHT BLINK",
    # 11 => "Same home + unit: ONE LIGHT STOP DIMMING",
    # 12 => "Same home + unit: PRESET BRIGHTNESS LEVEL",
    # 13 => "Status feedback: ON",
    # 14 => "Status feedback: OFF",
    # 15 => "Status REQUEST",
    # 16 => "Setup main address of RECEIVER",
    # 17 => "Setup main address of TRANSMITTER",
    # 18 => "Setup scene address",
    # 19 => "Clear scene address under the same HOME + UNIT",
    # 20 => "Clean all the scene addresses in each receiver",
    # 21 => "FUTURE USE",
    # 22 => "FUTURE USE",
    # 23 => "FUTURE USE",
    # 24 => "Check signal strength",
    # 25 => "Check noise strength",
    # 26 => "Report signal strength",
    # 27 => "Report noise strength",
    # 28 => "Check the ID PULSE in the same USER + HOME",
    # 29 => "Check the only ON id pulse in the same USER + HOME",
    # 30 => "Report ALL id pulse (3-phase power line only",
    # 31 => "Report only ON pulse (3-pgase power line only"

import sys, serial
from xPLAPI import *
from struct import *
from time import localtime, strftime


myxpl = Manager(ip = "0.0.0.0",source = "domopyx-PLCBUS-1141.domix", port = 50010)
ser = serial.Serial(5, 9600, timeout=2, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=0) #, rtscts=1)

# Commands PLCBUS
''' ALL_USER_UNIT_OFF must be with home unit=00 '''
cmd_plcbus = {  'ALL_UNITS_OFF':         '00',
                'ALL_LIGHTS_ON':         '01',
                'ON':                    '02',
                'OFF':                   '03',
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

# constants
code_value = {'A':0, 'B':1, 'C':2, 'D':3, 'E':4, 'F':5, 'G':6, 'H':7, 'I':8, 'J':9, 'K':10, 'L':11, 'M':12, 'N':13, 'O':14, 'P':15}

print strftime("%Y-%m-%d %H:%M:%S")

def plcbus_cmd(message):
    def convert_device(value):
        tempo = int(dev[1:]) - 1
        tempo2 = '%01X%01x' % (code_value[dev[0]], tempo)
        return tempo2
    level = 0
    tech = message.get_key_value('techno')
    c_house = message.get_key_value('house')
    cmd = message.get_key_value('command')
    dev = message.get_key_value('device')
    if tech == 'PLCBUS':
        plcbus_frame = '0205FF%s%s000003' % (convert_device(dev), cmd_plcbus[cmd]) #, int(level))
        plcbus_frame_on='\x02\x05\xFF\xB0\x22\x00\x00\x03'
        print "frame ok  :   " + plcbus_frame_on
        for i in range(3):
            ser.write(plcbus_frame.decode("hex"))
        s = ser.read(size=9)
        print "return frame  :   " + s
        dt = localtime()
        mess = Message()
        dt = strftime("%Y-%m-%d %H:%M:%S")
        mess.set_type("xpl-trig")
        mess.set_schema("x10.basic")
        mess.set_data_key("datetime", dt)
        mess.set_data_key("command", cmd)
        mess.set_data_key("device", dev)
        myxpl.send(mess)
    print "sendind frame :   " + plcbus_frame.decode("hex")
    print "sendind frame r : " + plcbus_frame
    print "CMD : %s - DEV : %s - HOUSE : %s" % (cmd, dev, c_house)

# use x10.basic to test
general = Listener(plcbus_cmd, myxpl, {'schema':'x10.basic','type':'XPL-TRIG'}) 

# ser.close()
