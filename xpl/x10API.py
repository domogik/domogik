#!/usr/bin/python
# -*- encoding:utf-8 -*-

# $LastChangedBy: mschneider $
# $LastChangedDate: 2008-07-21 09:38:29 +0200 (lun. 21 juil. 2008) $
# $LastChangedRevision: 91 $

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
    def __init__(self):
        res = Popen("heyu -c /etc/heyu/x10.conf start", shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            raise X10Exception, "Error during Heyu init"
        self._housecodes = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
        self._unitcodes = [ i+1 for i in range(16) ]

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
        heyucmd = "heyu -c /etc/heyu/x10.conf %s %s" % (cmd, item)
        print heyucmd
        res = Popen(heyucmd, shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            raise X10Exception, "Error during send of command"
 
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
#        try:
        self._valid_item(item)
        self._send("off", item)
#        except:
#            return False
#        else:
#            return True

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
        @param item : the item to send the ALLOFF order to
        @Return True if order was sent, False in case of errors
        """
        try:
            self._valid_house(house)
            self._send("alloff", house)
        except:
            return False
        else:
            return True
