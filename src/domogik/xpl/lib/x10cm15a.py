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

X10 technology support using cm15a

Implements
==========

- X10Exception.__init__(self, value)
- X10Exception.__str__(self)
- X10API.__init__(self, device)
- X10API._valid_item(self, item)
- X10API._valid_house(self, house)
- X10API._send(self, cmd, item)
- X10API._send_lvl(self, cmd, item, lvl)
- X10API.on(self, item)
- X10API.off(self, item)
- X10API.house_on(self, house)
- X10API.house_off(self, house)
- X10API.bright(self, item, lvl)
- X10API.brightb(self, item, lvl)
- X10API.dim(self, item, lvl)
- X10API.dimb(self, item, lvl)
- X10API.lights_on(self, house)
- X10API.lights_off(self, house)
- X10Monitor.__init__(self, device)
- X10Monitor.get_monitor(self)
- X10Monitor.__init__(self, pipe)
- X10Monitor.add_cb(self, cb)
- X10Monitor.del_cb(self, cb)
- X10Monitor.run(self)
- X10Monitor._call_cbs(self, units, order, arg)
- HeyuManager.__init__(path)
- HeyuManager.load()
- HeyuManager.restart()
- HeyuManager.write()

@author: Matthieu Bollot <mattboll@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import traceback
import time
from struct import pack


class X10Exception(Exception):
    """
    X10 exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class X10API:
    """
    This class define some facilities to use X10.
    It's based on cm15a driver, you need to have it installed
    """

    def __init__(self, device, log):
        if not os.path.exists(device):
            raise X10Exception(
                  "Device %s does not exist, can't use this cm15a device" %
                  device)
        self._log = log
        try:
            self._cm15a = os.open('/dev/cm15a0', os.O_RDWR)
            self._log.info("cm15a device opened")
        except:
            error = "Error while opening cm15a device : %s : %s" % (device, 
                    str(traceback.format_exc()))
            raise X10Exception(error)
        self._housecodes = list('ABCDEFGHIJKLMNOP')
        self._unitcodes = range(1, 17)
        self._device = device
        self.house_code = 'A'

    def close(self):
        """ close cm15a device
        """
        self._log.info("Close cm15a device")
        try:
            self._log.info("Close cm15a device")
            os.close(self._cm15a)
        except:
            error = "Error while closing modem device"
            raise X10Exception(error)

    def _valid_item(self, item):
        """
        Check an item to have good 'HU' syntax
        Raise exception if it is not
        """
        house, unit = (item[0].upper(), item[1])
        try:
            if not (house in self._housecodes and int(unit) in self._unitcodes):
                raise AttributeError
        except:
            self._log.warning("Invalid item %s%s, must be 'HU'" % (house, unit))

    def _convert_address(self, device):
        """
        converti commande version humaine, en hexa
        OMG je m'apprÃªte Ã  faire un truc atroce que j'oserai pas regarder demain -_-'
        dÃ©solÃ© au prochain qui lira ce code donc sÃ»rement moiâ€¦
        """
        if (device[0] == 'A'):
            self.house_code = '6'
        elif (device[0] == 'B'):
            self.house_code = 'E'
        elif (device[0] == 'C'):
            self.house_code = '2'
        elif (device[0] == 'D'):
            self.house_code = 'A'
        elif (device[0] == 'E'):
            self.house_code = '1'
        elif (device[0] == 'F'):
            self.house_code = '9'
        elif (device[0] == 'G'):
            self.house_code = '5'
        elif (device[0] == 'H'):
            self.house_code = 'D'
        elif (device[0] == 'I'):
            self.house_code = '7'
        elif (device[0] == 'J'):
            self.house_code = 'F'
        elif (device[0] == 'K'):
            self.house_code = '3'
        elif (device[0] == 'L'):
            self.house_code = 'B'
        elif (device[0] == 'M'):
            self.house_code = '0'
        elif (device[0] == 'N'):
            self.house_code = '8'
        elif (device[0] == 'O'):
            self.house_code = '4'
        elif (device[0] == 'P'):
            self.house_code = 'C'

        if (device[1:] == '1'):
            item = '6'
        elif (device[1:] == '2'):
            item = 'E'
        elif (device[1:] == '3'):
            item = '2'
        elif (device[1:] == '4'):
            item = 'A'
        elif (device[1:] == '5'):
            item = '1'
        elif (device[1:] == '6'):
            item = '9'
        elif (device[1:] == '7'):
            item = '5'
        elif (device[1:] == '8'):
            item = 'D'
        elif (device[1:] == '9'):
            item = '7'
        elif (device[1:] == '10'):
            item = 'F'
        elif (device[1:] == '11'):
            item = '3'
        elif (device[1:] == '12'):
            item = 'B'
        elif (device[1:] == '13'):
            item = '0'
        elif (device[1:] == '14'):
            item = '8'
        elif (device[1:] == '15'):
            item = '4'
        elif (device[1:] == '16'):
            item = 'C'
        return '0x'+self.house_code+item

    def _convert_command(self, cmd):
        """
        convert a command such as on, off, dim to the hexa value which is 
        housecode/command. for example 0x62
        """
        if (cmd == 'alloff'):
            cmd = '0'
        elif (cmd == 'lightson'):
            cmd = '1'
        elif (cmd == 'on'):
            cmd = '2'
        elif (cmd == 'off'):
            cmd = '3'
        elif (cmd == 'dim'):
            cmd = '4'
        elif (cmd == 'bright'):
            cmd = '5'
        elif (cmd == 'lightsoff'):
            cmd = '6'
        elif (cmd == 'extendedcode'):
            cmd = '7'
        elif (cmd == 'hailrequest'):
            cmd = '8'
        elif (cmd == 'hailacknowledge'):
            cmd = '9'
        elif (cmd == 'presetdim1'):
            cmd = 'A'
        elif (cmd == 'presetdim2'):
            cmd = 'B'
        elif (cmd == 'extendeddatatransfert'):
            cmd = 'C'
        elif (cmd == 'statuson'):
            cmd = 'D'
        elif (cmd == 'statusoff'):
            cmd = 'E'
        elif (cmd == 'statusrequest'):
            cmd = 'F'
        return '0x'+self.house_code+cmd

    def _valid_house(self, house):
        """
        Check an house to have good 'H' syntax
        Raise exception if it is not
        """
        try:
            if house[0] not in self._housecodes:
                raise AttributeError
        except:
            self._log.warning(
                "Invalid house %s, must be 'H' format, between A and P" %
                (house[0].upper()))

    def _send(self, cmd, item):
        """
        Send a command trought cm15a
        @param cmd : Command to send ('ON','OFF', etc)
        @param item : Item to send order to (Can be HU or H form)
        """
        self._log.debug("cm15a command : %s" % cmd)
        self._log.debug("cm15a item : %s" % item)
        item_code = self._convert_address(item)
        cmd_code = self._convert_command(cmd)
        os.write(self._cm15a, pack("BB", 4, int(item_code, 16)))
        time.sleep(1)
        os.write(self._cm15a, pack("BB", 6, int(cmd_code, 16)))

    def _send_lvl(self, cmd, item, lvl):
        """
        Send a command trought heyu
        @param cmd : Command to send ('dim','bright', etc)
        @param item : Item to send order to (Can be HU or H form)
        @param lvl : level of light intensity (1-22), this is a relative value
        """
        item_code = self._convert_address(item)
        cmd_code = self._convert_command(cmd)
        self._log.debug("lvl received : %s" % lvl)
        """
        if ( lvl > 22 ):
            lvl = 22

        if ( lvl < 1 ):
            lvl = 1
        """
        lvl = min(int(lvl),22)
        lvl = max(int(lvl),0)
        self._log.debug("lvl received 2: %s" % lvl)

        lvl = lvl - 1
        # decalage de 3 bits sur la gauche les 3 derniers bits doivent etre 110
        lvl = lvl * 8 + 6
        self._log.debug("cm15a command : %s" % cmd)
        self._log.debug("cm15a item : %s" % item)
        self._log.debug("lvl : %s" % lvl)
        os.write(self._cm15a, pack("BB", 4, int(item_code, 16)))
        time.sleep(1)
        os.write(self._cm15a, pack("BBB", 6, int(cmd_code, 16),lvl))

    def on(self, item):
        """
        Send an ON order to the item element
        @param item : the item to send the ON order to
        @Return True if order was sent, False in case of errors
        """
        try:
            self._log.info("cm15 command on")
            self._valid_item(item)
            self._send("on", item)
        except:
            return False
        else:
            return True

    def off(self, item):
        """
        Send an OFF order to the item element
        @param item : the item to send the OFF order to
        @Return True if order was sent, False in case of errors
        """
        try:
            self._log.info("cm15 command off")
            self._valid_item(item)
            self._send("off", item)
        except:
            return False
        else:
            return True

    def house_on(self, house):
        """
        Send an ALLON order to the item element
        @param item : the item to send the ALLON order to
        @Return True if order was sent, False in case of errors
        """
        try:
            self._valid_house(house)
            self._send("allon", house)
        except:
            return False
        else:
            return True

    def house_off(self, house):
        """
        Send an ALLOFF order to the item element
        @param house: the item to send the ALLOFF order to
        @Return True if order was sent, False in case of errors
        """
        try:
            self._valid_house(house)
            self._send("alloff", house)
        except:
            return False
        else:
            return True

    def bright(self, item, lvl):
        '''
        Send bright command
        @param item : item to send brigth order
        @param lvl : bright level (1-22)
        @Return True if order was sent, False in case of errors
        '''
        try:
            self._valid_item(item)
            self._send_lvl("bright", item, lvl)
        except:
            return False
        else:
            return True

    def brightb(self, item, lvl):
        '''
        Send bright command after full brigth
        @param item : item to send bright order
        @param lvl : bright level (1-22)
        @Return True if order was sent, False in case of errors
        '''
        try:
            self._valid_item(item)
            self._send_lvl("brightb", item, lvl)
        except:
            return False
        else:
            return True

    def dim(self, item, lvl):
        '''
        Send dim command
        @param item : item to send brigth order
        @param lvl : dim level (1-22)
        @Return True if order was sent, False in case of errors
        '''
        self._valid_item(item)
        self._send_lvl("dim", item, lvl)

    def dimb(self, item, lvl):
        '''
        Send dim command after full brigth
        @param item : item to send dim order
        @param lvl : dim level (1-22)
        @Return True if order was sent, False in case of errors
        '''
        try:
            self._valid_item(item)
            self._send_lvl("dimb", item, lvl)
        except:
            return False
        else:
            return True

    def lights_on(self, house):
        """
        Send an lights_on order to the item element
        @param item : the house to send the lights_on order to
        @Return True if order was sent, False in case of errors
        """
        try:
            self._valid_house(house)
            self._send("lightson", house)
        except:
            return False
        else:
            return True

    def lights_off(self, house):
        """
        Send an lightsoff order to the item element
        @param house: the house to send the lightsoff order to
        @Return True if order was sent, False in case of errors
        """
        try:
            self._valid_house(house)
            self._send("lightson", house)
        except:
            return False
        else:
            return True

