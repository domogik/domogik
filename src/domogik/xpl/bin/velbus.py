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

Velbus usb support
=> based on rfxcom plugin

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-20012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.velbus import VelbusException
from domogik.xpl.lib.velbus import VelbusUSB
import threading

class VelbusUsbManager(XplPlugin):
    """
	Managages the velbus domogik plugin
    """
    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='velbus')
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('velbus', 'device')

        # Init RFXCOM
        self.manager  = VelbusUSB(self.log, self.send_xpl,
			self.send_trig, self.get_stop())
        
        # Create a listener for all messages used by RFXCOM
        Listener(self.process_lighting_basic, self.myxpl,
                 {'xpltype': 'xpl-cmnd', 'schema': 'lighting.basic'})
        # Create listeners
        try:
            self.manager.open(device)
        except VelbusException as ex:
            self.log.error(ex.value)
            self.force_leave()
            return
            
        # Start reading RFXCOM
        listenthread = threading.Thread(None,
                                   self.manager.listen,
                                   "velbus-process-reader",
                                   (self.get_stop(),),
                                   {})
        self.register_thread(listenthread)
        listenthread.start()
        self.enable_hbeat()

    def send_xpl(self, schema, data):
        """ Send xPL message on network
        """
        self.log.info("schema:%s, data:%s" % (schema, data))
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema(schema)
        for key in data:
            msg.add_data({key : data[key]})
	print msg
        self.myxpl.send(msg)

    def send_trig(self, message):
        """ Send xpl-trig given message
            @param message : xpl-trig message
        """
        self.myxpl.send(message)

    def process_lighting_basic(self, message):
        """ Process xpl chema lightning.basic
        """
        print message
        self.send_xpl("lighting.device", message.data)
	add = message.data['device'].split('-');
	chan = []
        chan.append(int(add[1]))
	address = add[0]
	if message.data["level"] == str(100):
	    self.log.debug("set relay on")
	    self.manager.send_relayon( address, chan )
	else:
	    self.log.debug("set relay off")
	    self.manager.send_relayoff( address, chan )


if __name__ == "__main__":
    VelbusUsbManager()
