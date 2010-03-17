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

X10 technology support using serial a CM11 controller

Implements
==========
- class X10Exception
- class X10Controller
- class X10API
- class X10Monitor
- class HeyuManager

@author: Dominique Pierre <dominique.pierre.jlm@orange.fr>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import re
import time
import string
import serial
from subprocess import *
import threading
from domogik.common import logger
from domogik.common.ordereddict import OrderedDict

class X10Exception:
    """ X10 exception
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.repr(self.value)


class X10Controller:
    """
    This class implements the low level acces to a CM11 controller thru a serial port,
    requieres PySerial.
    """

    def __init__(self, serialConf):
        l = logger.Logger('x10API')
        self._log = l.get_logger()
        self._retry = 3
        self._lastUnit = -1

        # Mutex for serial port acces
        self._lock = threading.Lock()
        self._timeout = serialConf['timeout']
        self._serialdevice = serial.Serial()

        # Port
        self._serialdevice.setPort(serialConf['port'])

        # Speed
        self._serialdevice.setBaudrate(serialConf['speed'])

        # Timeout
        self._serialdevice.setTimeout(serialConf['timeout'])

        # Parity
        self._serialdevice.setParity(serialConf['parity'])

        # Stop bit
        self._serialdevice.setStopbits(serialConf['stop_bits'])

        # Byte size
        self._serialdevice.setByteSize(serialConf['byte_size'])
        self._open()

    def _open(self):
        """
        Open the serial device.

        Open the serial device on which the CM11 is connected.
        Serial parameters are :4800 bauds, 8 bits, no parity, 1 stop bit, no handshake

        In case of power fail, the CM11 is restarted.
        """

        # Open the serial device
        self._serialdevice.open()

        # Check whether the CM11 has something to tell or not
        self._serialdevice.setTimeout(2)
        buff = self._serialdevice.read()

        # Restore timeout
        self._serialdevice.setTimeout(self._timeout)

        # Check whether the CM11 is gone in power fail or not
        if len(buff):
            if ord(buff[0]) == 0xa5:
                self._log.debug('CM11 powerfail revieve')
                # Send the current time
                t = time.localtime()
                buff = ''
                buff += chr(0x9b)
                buff += chr(t.tm_sec)
                tmp = t.tm_sec
                if t.tm_hour % 2:
                    tmp += 60
                buff += chr(tmp)
                buff += chr(t.tm_hour / 2)
                buff += chr(t.tm_yday & 0xff)
                tmp = t.tm_yday << 8
                tmp |= 1 << (t.tm_wday + 1)
                buff += chr(tmp & 0xff)
                tmp = 0x06 << 4
                tmp |= 0x04
                buff += chr(tmp)
                self._serialdevice.write(buff)
                buff = self._serialdevice.read()

    def _close(self):
        """
        Release the serial port.
        """

        self._serialdevice.close()
        self._serialdevice = None

    def _read(self, count = 1):
        """
        Read count caracters on the serial line.
        @Return a string containing the chars read
        """
        return self._serialdevice.read(count)

    def _read_line(self):
        """
        Read bytes until '\n' is not received.
        @Return a string containing the bytes read
        """
        return self._serialdevice.readline()

    def _write(self, buffer):
        """
        Write a string buffer to the serial device
        @param buffer : the string buffer to send
        """
        self._serialdevice.write(buffer)

    def send_cmd(self, x10unit, func):
        """
        Send an X10 commmand over the serial line.

        The command is encoded as the raw Cm11 house, unit & function codes.
        Extended protocol not yet supported.

        @param x10unit : a tuple containing the house code, the unit address and the dimming level
        @param func  : the function code
        @Return True if order was sent, False in case of errors
        """

        self._lock.acquire()

        # Unpack tuple
        house, unit, dimLvl = x10unit

        currentUnit = (house << 4) | unit
        if (self._lastUnit != currentUnit):
            self._lastUnit = currentUnit
            count = self._retry
            while --count:
                # Send header, read checksum and compare
                buff =''
                buff += chr(0x04)
                buff += chr(currentUnit)
                chk = (ord(buff[0]) + ord(buff[1])) & 0xff
                self._write(buff)
                res =  self._read()
                if len(res):
                    if chk == ord(res[0]):
                        break
                    else:
                        self._log.error('CM11 checksum header error: computed =0x%x, received = 0x%x' % (chk, ord(res[0])))
                else:
                    self._log.error('CM11 timeout while sending unit address')

            if not count:
                self._log.error('Too many retries on sending unit address, arborting')
                self._lastUnit = 0
                self._lock.release()
                return False

            # Wait for the CM11
            buff = ''
            buff += chr(0x00)
            self._write(buff)
            res =  self._read()
            if ord(res[0]) != 0x55:
                self._log.error('CM11 error: not ready, status = 0x%x' % (ord(res[0])))
                self._lastUnit = 0
                self._lock.release()
                return False

        count = self._retry
        while --count:
            #Send command, read checksum and compare
            buff =''
            hdr = (dimLvl << 3) | 0x06
            buff += chr(hdr)
            buff += chr((house << 4) | func)
            chk = (ord(buff[0]) + ord(buff[1])) & 0xff
            self._write(buff)
            res =  self._read()
            if len(res):
                if chk == ord(res[0]):
                    break
                else:
                   self._log.error('CM11 checksum command error: computed =0x%x, received = 0x%x' % (chk, ord(res[0])))
            else:
                self._log.error('CM11 timeout while sending unit command')

        if not count:
            self._log.error('Too many retries while sending unit command, arborting')
            self._lastUnit = 0
            self._lock.release()
            return False

        # Wait for the CM11
        buff = ''
        buff += chr(0)
        self._write(buff)
        res =  self._read()
        if ord(res[0]) != 0x55:
            self._log.error('CM11 error: not ready, status = 0x%x' % (ord(res[0])))
            self._lastUnit = 0
            self._lock.release()
            return False
        self._lock.release()
        return True

    def getRI(self):
        return self._serialdevice.getRI()

class X10API:
    """
    This class define some facilities to use X10.
    """
    # Dictionary of House codes vs. X10 code
    houseToX10 = {'A' : 0x06, 'B' : 0x0E, 'C' : 0x02, 'D' : 0x0A,
                  'E' : 0x01, 'F' : 0x09, 'G' : 0x05, 'H' : 0x0D,
                  'I' : 0x07, 'J' : 0x0F, 'K' : 0x03, 'L' : 0x0B,
                  'M' : 0x00, 'N' : 0x08, 'O' : 0x04, 'P' : 0x0C}

    # Dictionary of Device codes vs X10 code
    deviceToX10 = {1 : 0x06, 2  : 0x0E, 3  : 0x02, 4  : 0x0A, 5  : 0x01, 6 : 0x09,
                   7 : 0x05, 8  : 0x0D, 9  : 0x07, 10 : 0x0F, 11 : 0x03,
                  12 : 0x0B, 13 : 0x00, 14 : 0x08, 15 : 0x04, 16 : 0x0C}

    # Dictionary of function codes vs X10 code
    funcToX10 = {'ALL_UNITS_OFF': 0x00, 'ALL_LIGHTS_ON': 0x01, 'ON': 0x02, 'OFF': 0x03,
                 'DIM': 0x04, 'BRIGHT': 0x05, 'ALL_LIGHTS_OFF': 0x06, 'EXTENDED_CODE': 0x07,
                 'HAIL_REQUEST': 0x08, 'HAIL_ACK': 0x09, 'PRESET_DIM1': 0x0A, 'PRESET_DIM2': 0x0B,
                 'EXTENDED_DATA': 0x0C, 'STATUS_ON': 0x0D, 'STATUS_OFF': 0x0E, 'STATUS_REQUEST': 0x0F}

    def __init__(self, heyuconf, serial_port = 0):
        self._serialconf = {
                            'speed':4800,
                            'timeout':15,
                            'parity':serial.PARITY_NONE,
                            'stop_bits':serial.STOPBITS_ONE,
                            'byte_size':serial.EIGHTBITS
                            }
        self._serialconf['port'] = serial_port
        l = logger.Logger('x10API')
        self._log = l.get_logger()
        self._housecodes = list('ABCDEFGHIJKLMNOP')
        self._unitcodes = range(1, 17)
        self._heyuconf = heyuconf
        self._controller = X10Controller(self._serialconf)

    def _valid_item(self, item):
        """ Check an item to have good X10 syntax
        Raise exception if it is not
        """
        h, u = (item[0].upper(), item[1])
        try:
            if not (h in self._housecodes and int(u) in self._unitcodes):
                raise AttributeError
        except:
            self._log.warning("Invalid item %s%s, must be 'HU'" % (h, u))

    def _valid_house(self, house):
        """
        Check an house to have good 'H' syntax
        Raise exception if it is not
        """
        try:
            if house[0] not in self._housecodes:
                raise AttributeError
        except:
            self._log.warning("Invalid house %s, must be 'H' format, between "\
                    "A and P" % (house[0].upper()))

    def _resolveUnit(self, *args):
        """
        Parse the API's house & device parameters in 'args'. 'args'
        may be in one of the formats 'A1'/'A 1'/'A', '1'/'A', 1. The
        tuple (house, device) is returned, where house is 'A'-'P' and
        device is 1-16.
        @param item : the method arguments
        @Return a tuple containing the house code, the device code and the dimming level
        """

        errString = 'Parse args: '
        house, device, dimLevel = None, 1, 0
        numArgs = len(args)
        if numArgs < 1:
            raise X10Exception(errString + 'too few args')
        elif numArgs > 3:
            raise X10Exception(errString + 'too many args')

        houseDev = string.replace(string.upper(args[0]), ' ', '')
        house = houseDev[0][0]
        if len(houseDev) > 1:
            device = int(houseDev[1:])
            if numArgs > 1:
                dimLevel = int(args[1])
        elif numArgs > 1:
            device = int(args[1])
            if numArgs > 2:
                dimLevel = int(args[2])
        if not house or not device:
            raise X10Exception(errString + 'house or dev not specified')
        if house < 'A' or house > 'P' or device < 1 or device > 16 or dimLevel < 0 or dimLevel > 23:
            raise X10Exception(errString + 'house or dev not valid')

        return (X10API.houseToX10[house], X10API.deviceToX10[device], dimLevel)

    def on(self, *unitArgs):
        """
        Send an ON order to the item element
        @param item : the item to send the ON order to
        @Return True if order was sent, False in case of errors
        """
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['ON'])

    def off(self, *unitArgs):
        """
        Send an OFF order to the item element
        @param item : the item to send the OFF order to
        @Return True if order was sent, False in case of errors
        """
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['OFF'])

    def house_on(self, *unitArgs):
        """
        Send an ALLON order to the item element
        @param item : the item to send the ALLON order to
        @Return True if order was sent, False in case of errors
        """
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['ALL_LIGHTS_ON'])

    def house_off(self, *unitArgs):
        """
        Send an ALLOFF order to the item element
        @param house: the item to send the ALLOFF order to
        @Return True if order was sent, False in case of errors
        """
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['ALL_LIGHTS_OFF'])

    def bright(self, *unitArgs):
        """
        Send bright command
        @param item : item to send brigth order
        @param lvl : bright level in percent
        @Return True if order was sent, False in case of errors
        """
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['BRIGHT'])

    def brightb(self, *unitArgs):
        '''
        Send bright command after full brigth
        @param item : item to send bright order
        @param lvl : bright level in percent
        @Return True if order was sent, False in case of errors
        '''
        self._controller.send_cmd(apply(self._resolveUnit, (unitArgs[0], '23')), X10API.funcToX10['DIM'])
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['BRIGHT'])

    def dim(self, *unitArgs):
        '''
        Send dim command
        @param item : item to send brigth order
        @param lvl : dim level in percent
        @Return True if order was sent, False in case of errors
        '''
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['DIM'])

    def dimb(self, *unitArgs):
        '''
        Send dim command after full brigth
        @param item : item to send dim order
        @param lvl : dim level in percent
        @Return True if order was sent, False in case of errors
        '''
        self._controller.send_cmd(apply(self._resolveUnit, (unitArgs[0], '23')), X10API.funcToX10['BRIGHT'])
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['DIM'])

    def lights_on(self, *unitArgs):
        """
        Send an lights_on order to the item element
        @param item : the house to send the lights_on order to
        @Return True if order was sent, False in case of errors
        """
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['ALL_LIGHTS_ON'])

    def lights_off(self, *unitArgs):
        """
        Send an lightsoff order to the item element
        @param house: the house to send the lightsoff order to
        @Return True if order was sent, False in case of errors
        """
        self._controller.send_cmd(apply(self._resolveUnit, unitArgs), X10API.funcToX10['ALL_LIGHTS_OFF'])


class X10Monitor:
    """
    Manage heyu monitor output
    """

    def __init__(self, heyuconf):
        res = Popen(["heyu","-c",heyuconf,"monitor"], stdout=PIPE)
        self._reader = self.__x10MonitorThread(res)

    def get_monitor(self):
        """
        Returns the x10MonitorThread intance
        """
        return self._reader

    class __x10MonitorThread(threading.Thread):
        """
        Internal class
        Manage read of the pipe and call of callbacks
        """

        def __init__(self, pipe):
            """
            @param pipe : the Popen instance
            """
            threading.Thread.__init__(self)
            self._pipe = pipe
            self._cbs = []

        def add_cb(self, cb):
            """
            Add a callback method
            The callback needs to have 3 parameters : plugin name, command value and parameter
            """
            self._cbs.append(cb)

        def del_cb(self, cb):
            """
            Removes a previously added callback if exists
            """
            self._cbs.remove(cb)

        def run(self):
            """
            Starts to check the stdout line
            """
            units = []
            order = None
            arg = None
            out = None
            regex_order = re.compile(r".* ([a-zA-Z0-9]+) :[^:]+$")
            regex_unit = re.compile(r".* : h[uc] ([^ ]+).*$")
            regex_security = re.compile(r".*(Alert|Clear) : hu ([A-P][0-9]+).*$")
            try:
                while not self._pipe.stdout.closed and out != '':
                    out = self._pipe.stdout.readline()
                    if 'addr unit' in out:
                        units.append(out.split()[8].lower())
                    elif 'func' in out:
                        if "Alert" in out or "Clear" in out:
                            # RF Security device
                            (order, unit) = regex_security.sub(r"\1,\2", out).lower().split(",")
                            units = [unit]
                        else:
                            # Standard order
                            order = out.split()[4].lower()
                        if '%' in out:
                            arg = out.split()[9].replace('%','')
                    if units and order:
                        self._call_cbs(units, order, arg)
                        units = []
                        order = None
                        arg = None
            except ValueError:
                # The pipe is closed
                self._log.warning("The heyu-monitor pipe is closed. Finish silently.")
                pass

        def _call_cbs(self, units, order, arg):
            """
            Call all callbacks
            """
            for cb in self._cbs:
                for unit in units:
                    cb(unit, order, arg)


class HeyuManager:
    """
    This class manages the heyu configuration file
    """

    ITEMS_SECTION = OrderedDict()
    ITEMS_SECTION['general'] = ['TTY','TTY_AUX','LOG_DIR', 'HOUSECODE', 'REPORT_PATH',
            'DEFAULT_MODULE','START_ENGINE','DATE_FORMAT','LOGDATE_YEAR','TAILPATH',
            'HEYU_UMASK', 'STATUS_TIMEOUT', 'SPF_TIMEOUT','TRANS_DIMLEVEL']
    ITEMS_SECTION['aliases'] = ['ALIAS']
    ITEMS_SECTION['scenes'] = ['SCENE', 'USERSYN', 'MAX_PPARMS']
    ITEMS_SECTION['scripts'] = ['SCRIPT','SCRIPT_MODE', 'SCRIPT_CTRL']
    ITEMS_SECTION['scheduler'] = ['SCHEDULE_FILE','MODE','PROGRAM_DAYS','COMBINE_EVENTS',
            'COMPRESS_MACROS','REPL_DELAYED_MACROS', 'WRITE_CHECK_FILES']
    ITEMS_SECTION['dawnduk'] = ['LONGITUDE','LATITUDE','DAWN_OPTION','DUSK_OPTION',
            'MIN_DAWN','MAX_DAWN','MIN_DUSK','MAX_DUSK']

    def __init__(self, path):
        """
        @param path = The heyu config file path, must be absolute
        """
        self._file = "%s" % path

    def load(self):
        """
        Load the file and parse it
        @return a list containing all the *uncommented* lines of config file
        """
        f = open(self._file, "r")
        lines = f.readlines()
        f.close()
        result = []
        for line in lines:
            if not line.startswith("#") and line.strip() != "":
                result.append(line.strip())
        return result

    def write(self, data):
        """
        Write config datas in the config file
        @param data : list of config lines
        @Warning : it will erease the previous config file
        @raise IOError if the file can'"t be opened
        """
        f = open(self._file, "w")
        for section in self.ITEMS_SECTION:
            f.write("##### %s #####\n\n" % section)
            for item in self.ITEMS_SECTION[section]:
                for d in data:
                    if d.startswith("%s " % item) or d.startswith("%s\t" % item):
                        f.write("%s\n" % d)
            f.write("\n")
        f.close()

    def restart(self):
        """
        Restart heyu process, needed to reload config
        @return the output of heyu restart command on stderr,
        should be empty if everything goes well
        """
        return ""

