#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

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

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-02-17 14:23:34 +0100 (mar. 17 févr. 2009) $
# $LastChangedRevision: 365 $

from subprocess import *
class X10Exception:
    """
    X10 exception
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.repr(self.value)

class X10API:
    """
    This class define some facilities to use X10.
    It's based on heyu software, you need to have it installed
    and heyu binaries must be in your PATH
    """
    def __init__(self, heyuconf):
        res = Popen("heyu -c " + heyuconf + " start", shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            print "Output was : %s" % output
            print "Heyu conf : %s" % heyuconf
            raise X10Exception, "Error during Heyu init" 
        self._housecodes = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
        self._unitcodes = [ i+1 for i in range(16) ]
        self._heyuconf = heyuconf

    def _valid_item(self, item):
        """
        Check an item to have good 'HU' syntax
        Raise exception if it is not
        """
        try:
            if ( item[0].upper() not in self._housecodes ) or ( int(item[1]) not in self._unitcodes ):
                raise X10Exception, "Invalid item, must be 'HU'"
        except:
            raise X10Exception, "Invalid item, must be 'HU'"

    def _valid_house(self, house):
        """
        Check an house to have good 'H' syntax
        Raise exception if it is not
        """
        try:
            if house[0] not in self._housecodes:
                raise X10Exception, "Invalid house, must be 'H' format, between A and P"
        except:
            raise X10Exception, "Invalid house, must be 'H' format, between A and P"

    def _send(self, cmd, item):
        """
        Send a command trought heyu
        @param cmd : Command to send ('ON','OFF', etc)
        @param item : Item to send order to (Can be HU or H form)
        """
        heyucmd = "heyu -c %s %s %s" % (self._heyuconf, cmd, item)
        print heyucmd
        res = Popen(heyucmd, shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            raise X10Exception, "Error during send of command : %s " % output

    def _send_lvl(self, cmd, item, lvl):
        """
        Send a command trought heyu
        @param cmd : Command to send ('ON','OFF', etc)
        @param item : Item to send order to (Can be HU or H form)
        """
        heyucmd = "heyu -c %s %s %s %s" % (self._heyuconf, cmd, item, lvl)
        print heyucmd
        res = Popen(heyucmd, shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            raise X10Exception, "Error during send of command : %s " % output

    def on(self, item):
        """
        Send an ON order to the item element
        @param item : the item to send the ON order to
        @Return True if order was sent, False in case of errors
        """
        try:
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
        @param lvl : bright level in percent
        @Return True if order was sent, False in case of errors
        '''
        try:
            self._valid_item(item)
            level = int(lvl * 0.22)
            if level == 0:
                level = 1
            self._send_lvl("bright", item, level)
        except:
            return False
        else:
            return True

    def brightb(self, item, lvl):
        '''
        Send bright command after full brigth
        @param item : item to send bright order
        @param lvl : bright level in percent
        @Return True if order was sent, False in case of errors
        '''
        try:
            self._valid_item(item)
            level = int(lvl * 0.22)
            if level == 0:
                level = 1
            self._send_lvl("brightb", item, level)
        except:
            return False
        else:
            return True

    def dim(self, item, lvl):
        '''
        Send dim command
        @param item : item to send brigth order
        @param lvl : dim level in percent
        @Return True if order was sent, False in case of errors
        '''
#        try:
        self._valid_item(item)
        level = int(lvl * 0.22)
        if level == 0:
            level = 1
        self._send_lvl("dim", item, level)
#        except:
#            print "Exception lors de l'envoi de dim"
#            return False
#        else:
#            return True

    def dimb(self, item, lvl):
        '''
        Send dim command after full brigth
        @param item : item to send dim order
        @param lvl : dim level in percent
        @Return True if order was sent, False in case of errors
        '''
        try:
            self._valid_item(item)
            level = int(lvl * 0.22)
            if level == 0:
                level = 1
            self._send_lvl("dimb", item, level)
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
