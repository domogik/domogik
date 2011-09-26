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

@author: Mika64 <ricart.michael@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""



from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.zwave import ZWave
from time import sleep

class Zwave(XplPlugin):
    def __init__(self):
        XplPlugin.__init__(self, name = 'zwave')
        Listener(self.zwave_cmd_cb, self.myxpl,{'schema': 'zwave.basic',
                                                 'xpltype': 'xpl-cmnd'})
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('zwave', 'device')
        speed = self._config.query('zwave', 'speed')
        print(device, '  ', speed)
#        device='/dev/ttyUSB0'
        self.myzwave = ZWave(device, speed, self.zwave_cb, self.log)
        self.myzwave.start()
        self.enable_hbeat()
        self.myzwave.send('Network Discovery')
        sleep(3)

    def zwave_cmd_cb(self, message):
        if 'command' in message.data:
            cmd = message.data['command']
            node = message.data['node']
            if cmd == 'level':
                lvl = message.data['level']
                self.myzwave.send(cmd, node, lvl)
            else:
                self.myzwave.send(cmd, node)

    def zwave_cb(self, read):
        mess = XplMessage()
        if 'info' in read:
            self.log.error ("Error : Node %s unreponsive" % read['node'])
	elif 'Find' in read:
	    print("node enregistré : %s" % read['Find'])
        elif 'event' in read:
            mess.set_type('xpl-trig')
            mess.set_schema('zwave.basic')
            mess.add_data({'event' : read['event'],
                           'node' : read['node'],
                           'level' : read['level']})
            self.myxpl.send(mess)
        elif 'command' in read and read['command'] == 'Info':
            print("Home ID is %s" % read['Home ID'])

if __name__ == "__main__":
    Zwave()
