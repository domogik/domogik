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

Nabaztag TTS support

Implements
==========

- NBZNotificationListener

@author: Kriss1
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik_packages.xpl.lib.nbz_tts import NBZNotification
from domogik.xpl.common.queryconfig import Query


class NBZNotificationListener(XplPlugin):
    """ Create listener for xPL messages about Nabaztag TTS notification
    """

    def __init__(self):
        """ Create listener for Nabaztag TTS notification
        """
        XplPlugin.__init__(self, name = 'nbz_tts')
        # Create logger
        self.log.debug("Listener for Nabaztag TTS notification created")

        # Configuration : list of nabaztag whith serial, token and voice
        self.alias_list = {}
        num = 1
        loop = True
        self._config = Query(self.myxpl, self.log)
        while loop == True:
            nabaztag = self._config.query('nbz_tts', 'name-%s' % str(num))
            server = self._config.query('nbz_tts', 'server-%s' % str(num))
            serial = self._config.query('nbz_tts', 'serial-%s' % str(num))
            token = self._config.query('nbz_tts', 'token-%s' % str(num))
            voice = self._config.query('nbz_tts', 'voice-%s' % str(num))
            if nabaztag != None:
                mess="Configuration : nabaztag=" + str(nabaztag) + " , server=" + str(server) + " , serial=" + str(serial) + ", token=" + str(token) + ", voice=" + str(voice)
                self.log.info(mess)
                print(mess)
                self.alias_list[nabaztag] = {"nabaztag" : nabaztag, "server" : server, "serial" : serial, "token" : token, "voice" : voice}
                num += 1
            else:
                loop = False

        # no nabaztag configured
        if num == 1:
            msg = "No nabaztag configured. Exiting plugin"
            self.log.info(msg)
            print(msg)
            self.force_leave()
            return

        # Check server
        for alias in self.alias_list:
            if str(self.alias_list[alias]['server']) != "None":
                self.log.debug("Server for nabaztag " + str(self.alias_list[alias]['nabaztag']) + " is " + str(self.alias_list[alias]['server']))
            else:
                self.log.error("Can't find the server adress for the nabaztag " + str(self.alias_list[alias]['nabaztag']) + " , please check the configuration page of this plugin")
                self.force_leave()
                return

        # Check serial
        for alias in self.alias_list:
            if str(self.alias_list[alias]['serial']) != "None":
                self.log.debug("Serial for nabaztag " + str(self.alias_list[alias]['nabaztag']) + " is " + str(self.alias_list[alias]['serial']))
            else:
                self.log.error("Can't find the serial for the nabaztag " + str(self.alias_list[alias]['nabaztag']) + " , please check the configuration page of this plugin")
                self.force_leave()
                return

        # Check token
        for alias in self.alias_list:
            if str(self.alias_list[alias]['token']) != "None":
                self.log.debug("Token for nabaztag " + str(self.alias_list[alias]['nabaztag']) + " is " + str(self.alias_list[alias]['token']))
            else:
                self.log.error("Can't find the Token for the nabaztag " + str(self.alias_list[alias]['nabaztag']) + " , please check the configuration page of this plugin")
                self.force_leave()
                return

        # Check voice
        for alias in self.alias_list:
            if str(self.alias_list[alias]['voice']) != "None":
                self.log.debug("Voice for nabaztag " + str(self.alias_list[alias]['nabaztag']) + " is " + str(self.alias_list[alias]['voice']))
            else:
                self.log.error("Can't find the Voice for the nabaztag " + str(self.alias_list[alias]['nabaztag']) + " , please check the configuration page of this plugin")
                self.force_leave()
                return


        # Create NBZNotification object
        self.nbz_notification_manager = NBZNotification(self.log)

        # Create listeners
        Listener(self.nbz_notification_cb, self.myxpl, {'schema': 'sendmsg.push', 'xpltype': 'xpl-cmnd'})
        self.enable_hbeat()

    def nbz_notification_cb(self, message):
        """ Call Nabaztag TTS lib
            @param message : message to send
        """
        self.log.debug("Call nbz_notification_cb")

        # mandatory keys
        if 'to' in message.data:
            to = message.data['to']
            for alias in self.alias_list:
                try:
                    if str(self.alias_list[alias]['nabaztag']) == str(to):
                        serverkey = self.alias_list[alias]['server']
                        serialkey = self.alias_list[alias]['serial']
                        tokenkey = self.alias_list[alias]['token']
                        voicekey = self.alias_list[alias]['voice']
                except :
                    self.log.debug("Can't find the recipient, please check the configuration page of this plugin")
                    self.force_leave()
                    return
        else:
            self.log.warning("No recipient was found in the xpl message")
            return

        if 'body' in message.data:
            body = message.data['body']
        else:
            self.log.warning("No message was found in the xpl message")
            return


        self.log.debug("Call send_tts with following parameters : server=" + serverkey + ", serial=" + serialkey + ", token=" + tokenkey + ", message=" + body + ", voice=" + voicekey)
        self.nbz_notification_manager.send_tts(serverkey, serialkey, tokenkey, body, voicekey)



if __name__ == "__main__":
    XN = NBZNotificationListener()
