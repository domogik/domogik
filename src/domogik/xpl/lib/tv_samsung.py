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

Samsung television control with EX-Link

Implements
==========

- SamsungTv

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import binascii
import serial
from tv_samsung_led import COMMANDS
import sys


class SamsungTVException(Exception):  
    """                                                                         
    Samsung television control exception                                                           
    """                                                                         
                                                                                
    def __init__(self, value):                                                  
        Exception.__init__(self)
        self.value = value                                                      
                                                                                
    def __str__(self):                                                          
        return repr(self.value)           


class SamsungTV:
    """ Control samsung television
    """

    def __init__(self, log = None):
        """ Init samsung TV controller
        """
        self._log = log
        self._samsung = None


    def open(self, device):
        """ Open EX Link
            @param device : serial port connected to EX Link
        """
        try:
            print("Try to open Samsung EX Link device : %s" % device)
            self._samsung = serial.Serial(device, 9600, 
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                xonxoff=serial.XOFF)
            print("EX Link device opened")
        except:
            error = "Error while opening EX Link device : %s. Check if it is the good device or if you have the good permissions on it." % device
            raise SamsungTVException(error)


    def send(self, cmd_alias, param = None):
        """ Send command code associated to alias to EX Link
            @param cmd_alias : alias 
            @param param : command parameter 
        """
        print("Call command '%s' with parameter '%s'" % (cmd_alias, param))
        if not cmd_alias in COMMANDS:
            print("Command not known : '%s'" % cmd_alias)
            return
        cmd = self.generate_command(COMMANDS[cmd_alias], param)
        print("Code for command : '%'" % cmd)
        data = binascii.unhexlify(cmd)
        self._samsung.write("%s" % data)
        # TODO : get return for command
        #res = ser.read(16)
        #print("res=%s" % res)
        return True

    def generate_command(self, cmd, param = None):
        """ Generate command with header and checksum
            @param cmd : command
            @param param : parameter for command (volume level, channel number) 
        """
        # TODO : use param
        header = "0822"
        data = cmd.decode("hex")
        sum = 0
        for byte in data:
            sum += ord(byte)
        sum += 42
        cs = self.get_checksum(header + cmd)
        return header + cmd + cs

    def close(self):
        """ Close EX Link
        """
        self._samsung.close()

    def get_checksum(value):
        """ Generate checksum
            @param value : value for which we want a checksum
        """
        data = value.decode("hex")
        sum = 0
        for byte in data:
            sum += ord(byte)
        data = hex((~sum + 1) & 0xFF)
        data = str(data)[2:]
        if len(data) < 2:    
           data = '0' + data
        return data

if __name__ == "__main__":
    my_tv = SamsungTV(None)
    my_tv.open(0)
    my_tv.send(sys.argv[1])
    my_tv.close()
