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

Iphone Push Notification support

Based on external service provide by pushme.to


Implements
==========

- IPushNotificationListener

@author: Kriss1
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.lib.ipushnot import IPushNotification
from domogik.xpl.common.queryconfig import Query


class IPushNotificationListener(XplPlugin):
    """ Create listener for xPL messages about Iphone push notification
    """

    def __init__(self):
        """ Create listener for Iphone push notification
        """
        XplPlugin.__init__(self, name = 'ipushnot')
        # Create logger
        self.log.debug("Listener for Iphone push notification created")

        # Get configuration
        self._config = Query(self.myxpl, self.log)
        self._pushmenick = str(self._config.query('ipushnot','pushmenick'))
        self._signature = str(self._config.query('ipushnot','signature'))

        self.log.debug("Config : pushmenick = " + self._pushmenick)
        self.log.debug("Config : signature = " + self._signature)

        # Create IPushNotification object
        self.ipn_notification_manager = IPushNotification(self.log)

        # Create listeners
        Listener(self.ipn_notification_cb, self.myxpl, {'schema': 'sendmsg.basic', 'xpltype': 'xpl-cmnd'})
        self.enable_hbeat()

    def ipn_notification_cb(self, message):
        """ Call Iphone notification lib
            @param message : message to send
        """
        self.log.debug("Call ipn_notification_cb")

        if 'body' in message.data:
            body = message.data['body']

        self.log.debug("Call send_ipn")
        self.ipn_notification_manager.send_ipn(self._pushmenick, body, self._signature)


if __name__ == "__main__":
    IN = IPushNotificationListener()
