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

Command Relay on Foscam camera

Implements
==========


@author: capof <capof1000 at gmail.com>
@copyright: (C) 2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import XplTimer
#import struct
from threading import Thread, Event
import subprocess
import time
import traceback
#mod
import urllib
import time

class RELAY:
    """
    This class allow to use Wake on Lan
    """

    def __init__(self, log):
        """
        Init object
        @param log : logger instance
        """
        self._log = log

    def pulse_relay(self, ip, port, user, password, delay,device):
        # future PULSE
        """
        Close the relay and open it after delay duration
        """
        self._log.info("Start processing Pulse Command on %s  " % (device))
        
        try:
            self.url1 = "http://%s:%s/decoder_control.cgi?command=94&user=%s&pwd=%s" % (ip, port, user, password)
            #print self.url1
            #f = urllib.urlopen("http://192.168.1.32/decoder_control.cgi?command=94&user=admin&pwd=")
            f = urllib.urlopen( self.url1)
            self._log.debug("Trying to acces to First Pulse URL  %s  " % (self.url1))
            if f.read().strip() == "ok.":
                 #print "premier ok"
                 self._log.debug("First Pulse Url response %s  " % (f.read().strip()))
                 self._log.debug("Waiting for %s seconds to acces the second URL  " % (delay))
                 time.sleep(delay)
                 self.url2 = "http://%s:%s/decoder_control.cgi?command=95&user=%s&pwd=%s" % (ip, port, user, password)
                 #print self.url2
                 #f = urllib.urlopen("http://192.168.1.32/decoder_control.cgi?command=95&user=admin&pwd=")
                 f = urllib.urlopen( self.url2)
                 self._log.debug("Trying to acces to Second Pulse URL  %s  " % (self.url2))
                 if f.read().strip() == "ok.":
                      #print "second ok"
                      self._log.debug("Second Pulse Url response %s  " % (f.read().strip()))
                      return True
                 else:
                      self._log.error("Fail to acces Second Pulse URL : %s" % traceback.format_exc())
                 return False
            else:
                 self._log.error("Fail to acces First Pulse URL : %s" % traceback.format_exc())
                 return False


        except:
            self._log.error("Fail to pulse Foscam relay : %s" % device)
            return False

    def close_relay(self, ip, port, user, password,device):
        """
        close the relay 
        """
        self._log.info("Start processing Close Command on %s  " % (device))
        
        try:
            self.url1 = "http://%s:%s/decoder_control.cgi?command=94&user=%s&pwd=%s" % (ip, port, user, password)
            #print self.url1 
            f = urllib.urlopen("http://192.168.1.32/decoder_control.cgi?command=94&user=admin&pwd=")
            self._log.debug("Trying to acces to Close URL  %s  " % (self.url1))
            if f.read().strip() == "ok.":
               self._log.debug("Close Command Url response %s  " % (f.read().strip()))
               return True
            else:
               self._log.error("Fail to closed Foscam relay : %s" % traceback.format_exc())
               return False
        except:
            self._log.error("Fail to close Foscam relay : %s" % traceback.format_exc())
            return False

    def open_relay(self, ip, port, user, password):
        """
        Open the relay
        """
        self._log.info("Start processing Open Command on %s  " % (device))
        
        # Order the relay to open 

        try:
            self.url1 = "http://%s:%s/decoder_control.cgi?command=95&user=%s&pwd=%s" % (ip, port, user, password)
            #f = urllib.urlopen("http://192.168.1.32/decoder_control.cgi?command=95&user=admin&pwd=")
            self._log.debug("Trying to acces to Open URL  %s  " % (self.url1))
            f = urllib.urlopen( self.url1)
            if f.read().strip() == "ok.":
               self._log.info("Foscam relay opened suscessfully : %s" % traceback.format_exc())
               return True
            else:
               self._log.error("Fail to open Foscam relay : %s" % traceback.format_exc())
               return False
        except:
            self._log.error("Fail to open Foscam relay : %s" % traceback.format_exc())
