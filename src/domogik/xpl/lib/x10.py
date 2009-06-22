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

X10 technology support

Implements
==========

- X10Exception:.__init__(self, value)
- X10Exception:.__str__(self)
- X10API:.__init__(self, heyuconf)
- X10API:._valid_item(self, item)
- X10API:._valid_house(self, house)
- X10API:._send(self, cmd, item)
- X10API:._send_lvl(self, cmd, item, lvl)
- X10API:.on(self, item)
- X10API:.off(self, item)
- X10API:.house_on(self, house)
- X10API:.house_off(self, house)
- X10API:.bright(self, item, lvl)
- X10API:.brightb(self, item, lvl)
- X10API:.dim(self, item, lvl)
- X10API:.dimb(self, item, lvl)
- X10API:.lights_on(self, house)
- X10API:.lights_off(self, house)
- X10Monitor:.__init__(self, heyuconf)
- X10Monitor:.get_monitor(self)
- X10Monitor:.__init__(self, pipe)
- X10Monitor:.add_cb(self, cb)
- X10Monitor:.del_cb(self, cb)
- X10Monitor:.run(self)
- X10Monitor:._call_cbs(self, units, order, arg)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from subprocess import *
import threading
from domogik.common import logger


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
        l = logger.Logger('x10API')
        self._log = l.get_logger()
        res = Popen("heyu -c " + heyuconf + " start", shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            self._log.error("Output was : %s\nHeyu config file path is : %s" \
                    % (output, heyuconf))
            raise X10Exception("Something went wrong with heyu. check logs")
        self._housecodes = list('ABCDEFGHIJKLMNOP')
        self._unitcodes = range(1, 17)
        self._heyuconf = heyuconf

    def _valid_item(self, item):
        """
        Check an item to have good 'HU' syntax
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

    def _send(self, cmd, item):
        """
        Send a command trought heyu
        @param cmd : Command to send ('ON','OFF', etc)
        @param item : Item to send order to (Can be HU or H form)
        """
        heyucmd = "heyu -c %s %s %s" % (self._heyuconf, cmd, item)
        self._log.debug("Heyu command : %s" % heyucmd)
        res = Popen(heyucmd, shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            self._log.error("Error during send of command : %s " % output)

    def _send_lvl(self, cmd, item, lvl):
        """
        Send a command trought heyu
        @param cmd : Command to send ('ON','OFF', etc)
        @param item : Item to send order to (Can be HU or H form)
        """
        heyucmd = "heyu -c %s %s %s %s" % (self._heyuconf, cmd, item, lvl)
        self._log.debug("Heyu command : %s" % heyucmd)
        res = Popen(heyucmd, shell=True, stderr=PIPE)
        output = res.stderr.read()
        res.stderr.close()
        if output:
            self._log.error("Error during send of command : %s " % output)

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
            level = int(int(lvl) * 0.22)
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
            level = int(int(lvl) * 0.22)
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
        level = int(int(lvl) * 0.22)
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
            level = int(int(lvl) * 0.22)
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
            The callback needs to have 3 parameters : module name, command value and parameter
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
            try:
                while not self._pipe.stdout.closed and out != '':
                    out = self._pipe.stdout.readline()
                    print "communicate %s" % out
                    if 'sndc addr unit' in out:
                        units.append(out.split()[8].lower())
                    elif 'sndc func' in out:
                        order = out.split()[4].lower()
                        if '%' in out:
                            arg = out.split()[9].replace('%','')
                    if units and order:
                        self._call_cbs(units, order, arg)
                        units = []
                        order = None
                        arg = None
            except ValueError:
                #The pipe is closed
                print "Exception"
                pass

        def _call_cbs(self, units, order, arg):
            """
            Call all callbacks 
            """
            for cb in self._cbs:
                for unit in units:
                    cb(unit, order, arg)


