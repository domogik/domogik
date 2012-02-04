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

XBMC Notification support

Implements
==========

- XBMCNotification.__init
- XBMCNotification.notify

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import threading
import time
import urllib


class XBMCNotification:
    """ This class allow to send notifications to XBMC
    """

    def __init__(self, log, address, delay, maxdelay):
        """ Init data
            @param log : log instance
            @param address : XBMC HTTP server address
            @param delay : default display delay
            @param maxdelay : maxdelay between title and text messages
        """
        # Init logger
        self._log = log
        self._log.info("XBMCNotification:__init")
        # Config
        self._xbmc_address = address
        self._maxdelay_between_actions = float(maxdelay)
        self._default_display_delay = delay
        # Persistent data
        self._last_action = time.time()
        self._title = ""
        self._text = ""
        self._title_received = 0
        self._text_received = 0
        self._delay = 0
        self._current_action = 0

    def notify(self, command, text, row, delay):
        """ Send notification to XBMC
            @param command : command part of xPL message
            @param text : text part of xPL message
            @param row : row part of xPL message
            @param delay : delay part of xPL message
        """
        self._log.info("Start process for notification on XBMC (" + \
                       self._xbmc_address + ")")
        row = int(row)
        delay = int(delay)

        self._current_action = time.time()
        time_between_actions = float(self._current_action - self._last_action)

        # New notification
        self._log.debug("Time elapsed : " + str(time_between_actions))
        self._log.debug("Max delay : " + str(self._maxdelay_between_actions))
        if time_between_actions > self._maxdelay_between_actions:
            self._log.debug("Time elapsed (" + str(time_between_actions) + \
                  ") for completing last notification : start new notification")
            self._title = ""
            self._text = ""
            self._title_received = 0
            self._text_received = 0

        if command == "WRITE":
            self._log.debug("COMMAND=WRITE")
            if row == 0:
                self._log.debug("ROW=0 : Title : " + text)
                self._title = text
                self._delay = delay
                self._title_received = 1
            if row == 1:
                self._log.debug("ROW=1 : Message : " + text)
                self._text = text
                self._delay = delay
                self._text_received = 1
            if delay == 0:
                self._delay = self._default_display_delay
                self._log.debug("DELAY=0 : setting default value : " + str(self._default_display_delay))
            else:
                self._delay = delay

            # All components of notification received
            if self._title_received and self._text_received:
                self._stop = threading.Event()
                self._thread = self._XBMCNotificationHandler(self._xbmc_address, self._title, self._text, self._delay)
                self._thread.run()
                self._title = ""
                self._text = ""
                self._title_received = 0
                self._text_received = 0

        self._last_action = self._current_action


    class _XBMCNotificationHandler(threading.Thread):
        """ Class for sending message in a thread
        """

        def __init__(self, xbmc_address, title, text, delay):
            """ Prepare data to send
                @param xbmc_address : xbmc adress
                @param title : notification title
                @param text : notification text
                @param delay : notification delay
            """
            # Initialize logger
            my_logger = logger.Logger('XBMC_MSG')
            self._log = my_logger.get_logger()
            self._log.debug("_XBMCNotificationHandler:__init__")
            # Parameters
            self._xbmc_address = xbmc_address
            self._title = urllib.quote(title)
            self._text = urllib.quote(text)
            self._delay = str(delay)+"000"
            # Initialize thread
            threading.Thread.__init__(self)

        def run(self):
            """ Call XBMC HTTP API to send notification
            """
            self._log.debug("_XBMCNotificationHandler:run")
            self._log.debug("NOTIF : title " + self._title)
            self._log.debug("NOTIF : text  " + self._text)
            self._log.debug("NOTIF : delay " + self._delay)
            try:
                self._log.debug("Call http://" + self._xbmc_address + \
                                "/xbmcCmds/xbmcHttp?command=ExecBuiltIn&parameter=XBMC.Notification(" + \
                                self._title + "," + self._text + "," + self._delay + ")")
                urllib.urlopen("http://" + self._xbmc_address + \
                               "/xbmcCmds/xbmcHttp?command=ExecBuiltIn&parameter=XBMC.Notification(" + \
                               self._title + "," + self._text + "," + self._delay + ")")
            except:
                self._log.error("Error while calling XBMC HTTP API")
