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

Caller id with a modem support

Implements
==========

- CIDManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.cidmodem import CallerIdModem
from domogik.xpl.lib.cidmodem import CallerIdModemException
import threading


class CIDManager(XplPlugin):
    """ Manage the modem to get CID
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='cidmodem')

        # Configuration
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('cidmodem', 'device')

        cid_command = self._config.query('cidmodem', 'cid-command')

        # Init Modem
        cid  = CallerIdModem(self.log, self.send_xpl)
        
        # Open Modem
        try:
            cid.open(device, cid_command)
        except CallerIdModemException as e:
            self.log.error(e.value)
            print(e.value)
            self.force_leave()
            return
            
        # Start reading Modem
        cid_process = threading.Thread(None,
                                   cid.listen,
                                   "listen_cid",
                                   (),
                                   {})                                  
        cid_process.start()                              
        self.enable_hbeat()

    def send_xpl(self, num):
        """ Send xPL message on network
            @param num : call number
        """
        print("Input call : %s " % num)
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema("cid.basic")
        msg.add_data({"calltype" : "INBOUND"})
        msg.add_data({"phone" : num})
        self.myxpl.send(msg)


if __name__ == "__main__":
    CIDManager()
