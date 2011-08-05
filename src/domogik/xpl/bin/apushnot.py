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

Android Push Notification support

Based on external service provide by Notifry


Implements
==========

- APushNotificationListener

@author: Kriss1
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.lib.apushnot import APushNotification
from domogik.xpl.common.queryconfig import Query


class APushNotificationListener(XplPlugin):
    """ Create listener for xPL messages about Android push notification
    """

    def __init__(self):
        """ Create listener for Android push notification
        """
        XplPlugin.__init__(self, name = 'apushnot')
        # Create logger
        self.log.debug("Listener for Android push notification created")

        # Configuration : list of recipient and source key
        self.alias_list = {}
        num = 1
        loop = True
        self._config = Query(self.myxpl, self.log)
        while loop == True:
            recipient = self._config.query('apushnot', 'name-%s' % str(num))
            source = self._config.query('apushnot', 'source-%s' % str(num))
            if recipient != None:
                self.log.info("Configuration : recipient=%s, source=%s" % 
                               (recipient, source))
                print ("Configuration : recipient=%s, source=%s" %
                               (recipient, source))
                self.alias_list[recipient] = {"recipient" : recipient,
                                       "source" : source}
                num += 1
            else:
                loop = False

        # no recipient configured
        if num == 1:
            msg = "No recipient configured. Exiting plugin"
            self.log.info(msg)
            print(msg)
            self.force_leave()
            return


        # Create APushNotification object
        self.apn_notification_manager = APushNotification(self.log)

        # Create listeners
        Listener(self.apn_notification_cb, self.myxpl, {'schema': 'sendmsg.push', 'xpltype': 'xpl-cmnd'})
        self.enable_hbeat()

    def apn_notification_cb(self, message):
        """ Call Android notification lib
            @param message : message from xpl
        """
        self.log.debug("Call apn_notification_cb")

        # mandatory keys
        if 'to' in message.data:
            to = message.data['to']

        if 'body' in message.data:
            body = message.data['body']

        # optionnal keys
        if 'title' in message.data:
            title = message.data['title']
        else:
            title = "default title"

        for alias in self.alias_list:
            try :
                if str(self.alias_list[alias]['recipient']) == str(to):
                    sourcekey = self.alias_list[alias]['source']
                    print("sourcekey=",sourcekey)
            except :
                self.log.debug("Can't find the recipient")


        self.log.debug("Call send_apn")
        self.apn_notification_manager.send_apn(sourcekey, title, body)


if __name__ == "__main__":
    IN = APushNotificationListener()
