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

TTS Text To Speech

Implements
==========

- TTS

@author: Gizmo - Guillaume MORLET <contact@gizmo-network.fr>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.tts import Tts

import traceback


class TtsManager(XplPlugin):
    """ Manage Tts
    """

    def __init__(self):
        """ Init manager
        """
        XplPlugin.__init__(self, name = 'tts')

        # Configuration

        self._config = Query(self.myxpl, self.log)
        software = self._config.query('tts', 'software')

        self.log.debug("Init info for tts created")
        ### Create tts objects
        self.my_tts = Tts(self.log)
	self.log.debug("Create object for tts created")
        # Create listener
        Listener(self.tts_cb, self.myxpl, {'schema': 'tts.basic','xpltype': 'xpl-cmnd'})
        self.log.debug("Listener for tts created")

        self.enable_hbeat()


    def tts_cb(self, message):
        """ Call tts lib
            @param message : xPL message detected by listener
        """
        # body contains the message
	self.log.debug("Function call back : entry")
        if 'speech' in message.data:
            speech = message.data['speech']
        else:
            self._log.warning("Xpl message : missing 'speech' attribute")
            return

        try:
	    self.log.debug("function call back : before send")
            self.my_tts.send(speech)
	    self.log.debug("function call back : after send")
        except:
	       self.log.error("Error while sending tts : %s" % traceback.format_exc())
              
               return



        

if __name__ == "__main__":
    inst = TtsManager()

