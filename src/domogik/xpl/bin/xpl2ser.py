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

Xpl bridge between ethernet and serial 

Implements
==========

TODO


@author: Kriss
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.xpl2ser import XplBridge
from domogik.xpl.lib.xpl2ser import XplBridgeException
import threading


class XplBridgeManager(XplPlugin):
    """ Send xpl message from hub to serial device
                    and vice versa
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='xpl2ser')

        # Configuration
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('xpl2ser', 'device')



        # Init serial device
        br  = XplBridge(self.log, self.send_xpl)
        

        # Create listeners
        Listener(self.xplbridge_cb, self.myxpl)
 

        # Open serial device
        try:
            br.open(device)
        except XplBridgeException as e:
            self.log.error(e.value)
            print(e.value)
            self.force_leave()
            return
            
        # Start reading serial device
        br_process = threading.Thread(None,
                                   br.listen,
                                   None,
                                   (),
                                   {})                                  
        br_process.start()                              
        self.enable_hbeat()

    def send_xpl(self, resp):
        """ Send xPL message on network
            @param resp : xpl message
        """
        print("Input xpl message : %s " % resp)
        msg = XplMessage(resp)
        self.myxpl.send(msg)

    def xplbridge_cb(self, message):
        """ Call xplbridge lib for sending xpl message to serial
            @param message : xpl message to send
        """
        self.log.debug("Call xplbridge_cb")
        mesg = message.to_packet()
        # Write on serial device
        self.log.debug("Call write() ")
        self.XplBridge.write(mesg)

if __name__ == "__main__":
    XplBridgeManager()

