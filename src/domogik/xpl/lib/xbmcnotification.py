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

XBMC Notification support

Implements
==========

- XBMCNotification.__init
- XBMCNotification._notify

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import threading
import time
from datetime import date
import urllib

from domogik.common import logger
from domogik.common.ordereddict import OrderedDict

class XBMCNotification:
    """
    This class allow to send notifications to XBMC
    """

    def __init__(self, address, delay, maxdelay):
        # Init logger
        l = logger.Logger('XBMC_MSG')
        self._log = l.get_logger()
        self._log.info("XBMCNotification:__init")
        # Config
        self._XBMCAddress = address
        self._maxDelayBetweenActions = float(maxdelay)
        self._defaultDisplayDelay = delay
        # Persistent data
        self._lastAction = time.time()
        self._title = ""
        self._text = ""
        self._titleReceived = 0
        self._textReceived = 0
        self._delay = 0

    def _notify(self, command, text, row, delay):
        """
        Send notification to XBMC
        """
        self._log.info("Start process for notification on XBMC (" + self._XBMCAddress + ")")
        row=int(row)
        delay=float(delay)

        self._currentAction = time.time()
        timeBetweenActions = float(self._currentAction - self._lastAction)

        # New notification 
        self._log.debug("Time elapsed : " + str(timeBetweenActions))
        self._log.debug("Max delay : " + str(self._maxDelayBetweenActions))
        if timeBetweenActions > self._maxDelayBetweenActions:
            self._log.debug("Time elapsed (" + str(timeBetweenActions) + ") for completing last notification : start new notification")
            self._title = "Domogik"
            self._text = ""
            self._titleReceived = 0
            self._textReceived = 0

        if command == "WRITE":
            self._log.debug("COMMAND=WRITE")
            if row == 0:
                self._log.debug("ROW=0 : Title : " + text)
                self._title = text
                self._delay = delay
                self._titleReceived = 1
            if row == 1:
                self._log.debug("ROW=1 : Message : " + text)
                self._text = text
                self._delay = delay
                self._textReceived = 1
            if delay == 0:
                self._delay = self._defaultDisplayDelay
                self._log.debug("DELAY=0 : setting default value : " + str(self._defaultDisplayDelay))
            else:
                self._delay = delay

            # All components of notification received
            if self._titleReceived and self._textReceived:
                self._stop = threading.Event()
                self._thread = self.__XBMCNotificationHandler(self._XBMCAddress, self._title, self._text, self._delay)
                self._thread.run()

            
        self._lastAction = self._currentAction


    class __XBMCNotificationHandler(threading.Thread):

        def __init__(self, XBMCAddress, title, text, delay):
            # Initialize logger
            l = logger.Logger('XBMC_MSG')
            self._log = l.get_logger()
            self._log.debug("__XBMCNotificationHandler:__init__")
            # Parameters
            self._XBMCAddress = XBMCAddress
            self._title = urllib.quote(title)
            self._text = urllib.quote(text)
            self._delay = str(delay)+"000"
            # Initialize thread
            threading.Thread.__init__(self)


        def run(self):
            self._log.debug("__XBMCNotificationHandler:run")
            self._log.debug("NOTIF : title " + self._title)
            self._log.debug("NOTIF : text  " + self._text)
            self._log.debug("NOTIF : delay " + self._delay)
            try:
                self._log.debug("Call http://" + self._XBMCAddress + "/xbmcCmds/xbmcHttp?command=ExecBuiltIn&parameter=XBMC.Notification(" + self._title + "," + self._text + "," + self._delay + ")")
                urllib.urlopen("http://" + self._XBMCAddress + "/xbmcCmds/xbmcHttp?command=ExecBuiltIn&parameter=XBMC.Notification(" + self._title + "," + self._text + "," + self._delay + ")")
                # in case we would want to make a pause on movie playing
                #self._log.debug("Call http://" + self._XBMCAddress + "/xbmcCmds/xbmcHttp?command=pause")
                #urllib.urlopen("http://" + self._XBMCAddress + "/xbmcCmds/xbmcHttp?command=pause")
            except:
                self._log.error("Error while calling XBMC HTTP API")




