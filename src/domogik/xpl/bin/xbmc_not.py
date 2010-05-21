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

Send Notiification message to XBMC

Implements
==========

- XBMCNotificationListener

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.lib.xbmc_not import XBMCNotification
from domogik.xpl.common.plugin import xPLResult
from domogik.xpl.common.queryconfig import Query

IS_DOMOGIK_PLUGIN = True
DOMOGIK_PLUGIN_TECHNOLOGY = "multimedia"
DOMOGIK_PLUGIN_DESCRIPTION = "Send notifications to XBMC"
DOMOGIK_PLUGIN_VERSION = "0.1"
DOMOGIK_PLUGIN_DOCUMENTATION_LINK = "http://wiki.domogik.org/tiki-index.php?page=plugins/XBMCNotification"
DOMOGIK_PLUGIN_CONFIGURATION=[
      {"id" : 0,
       "key" : "startup-plugin",
       "type" : "boolean",
       "description" : "Automatically start plugin at Domogik startup",
       "default" : "False"},
      {"id" : 1,
       "key" : "address",
       "type" : "string",
       "description" : "XBMC Media center HTTP API address(ip:port)",)
       "default" : ""},
      {"id" : 2,
       "key" : "delay",
       "type" : "number",
       "description" : "Default delay for displaying a notification (seconds)",
       "default" : 15},
      {"id" : 3,
       "key" : "maxdelay",
       "type" : "number",
       "description" : "Max delay between sending title and message with osd.basic xpl message (seconds)",
       "default" : 10}]



class XBMCNotificationListener(XplPlugin):
    """ Create listener for xPL messages about xbmc notifications
    """

    def __init__(self):
        """ Create lister for XBMC notifications
        """
        XplPlugin.__init__(self, name = 'xbmc_not')
        # Create logger
        self._log.debug("Listener for XBMC notifications created")

        # Get configuration
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('xbmc_not', 'address', res)
        address = res.get_value()['address']
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('xbmc_not', 'delay', res)
        delay = res.get_value()['delay']
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('xbmc_not', 'maxdelay', res)
        maxdelay = res.get_value()['maxdelay']

        self._log.debug("Config : address = " + address)
        self._log.debug("Config : delay = " + delay)
        self._log.debug("Config : maxdelay = " + maxdelay)

        # Create XBMCNotification object
        self.xbmc_notification_manager = XBMCNotification(address, delay, \
                                                         maxdelay)

        # Create listeners
        Listener(self.xbmc_notification_cb, self._myxpl, {'schema': 'osd.basic',
                'xpltype': 'xpl-cmnd'})


    def xbmc_notification_cb(self, message):
        """ Call XBMC notification lib
            @param message : message to send
        """
        self._log.debug("Call xbmc_notification_cb")

        if 'command' in message.data:
            command = message.data['command']
        if 'text' in message.data:
            text = message.data['text']
        if 'row' in message.data:
            row = message.data['row']
        if 'delay' in message.data:
            delay = message.data['delay']

        self._log.debug("Call _notify")
        self.xbmc_notification_manager.notify(command, text, row, delay)


if __name__ == "__main__":
    XN = XBMCNotificationListener()

