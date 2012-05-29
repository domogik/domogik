#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}$

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

Support Z-wave technology

Implements
==========

-Zwave

@author: Kriss <Kriss@domogik.org>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""



from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.pyozw import ZWave

class Zwave(XplPlugin):
    def __init__(self):
        XplPlugin.__init__(self, name = 'zwave')
        self.enable_hbeat()
        Listener(self.zwave_cmd_cb, self.myxpl,{'schema': 'zwave.basic',
                                                'xpltype': 'xpl-cmnd'})
        self._config = Query(self.myxpl, self.log)
        #serial_port = self._config.query('pyozw', 'device')
        #pyozw_path = self._config.query('pyozw', 'path')
        serial_port = "/dev/zwave"
        pyozw_path = "/usr/src/OpenZwave/py-openzwave"
        self.myzwave = ZWave(serial_port, pyozw_path, self.send_xpl)

    def zwave_cmd_cb(self, message):
        if 'command' in message.data:
            cmd = message.data['command']
            node = message.data['node']
            if cmd == 'level':
                lvl = message.data['level']
		print "level"
                #self.myzwave.sendLevel(node, lvl)
            elif cmd == 'on':
		print "on"
                self.myzwave.sendOn(node)
            elif cmd == 'off':
		print "off"
                #self.myzwave.sendOff(node) 
            elif cmd == 'info':
		print "info"
                #self.myzwave.sendInfo(node)

    def send_xpl(self, type, schema, resp):
        """ Send xPL message on network
        """
        msg = XplMessage()
        msg.set_type(type)
        msg.set_schema(schema)
        msg.add_data(resp)
        self.myxpl.send(msg)


if __name__ == "__main__":
    Zwave()

