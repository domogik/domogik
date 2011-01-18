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

-zwave

@author: Mika64 <ricart.michael@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.common import logger
from domogik.xpl.lib.zwave import *
from time import sleep
from threading import Event


class zwave(Helper):
    def __init__(self):
	self._event = Event()
        self.message = []
        self.commands = \
            { "find" :
                {
                "cb" : self.find,
                "desc" : "Show all nodes found on Z-wave network",
                },
              "info" :
                {
                "cb" : self.info,
                "desc" : "Show node info",
                "min_args" : 1,
                "usage" : "Show info for specified node <node id>",
                }
            }
        log = logger.Logger('zwave-helper')
        self._log = log.get_logger()
                
    def find(self, args = None):
        # Open device to find
        device = args[0]
        return ["Device = %s" % device]
        self.myzwave = ZWave(device, '115200', self._cb, self._log)
        self._log.error("Envoie de la trame")
        self.myzwave.send('Network Discovery')
        self._log.error("Trame envoyee, wait")
        self._event.wait()
        self._log.error("cb fini retour dans le find")
        self._event.clear()
        self.log.error("stopage du zwave")
        self.myzwave.stop()
        self._log.error("zwave stoppe")
        return self.message

    def info(self, args = None):
        node = args [0]
        self.myzwave.send('Info', node)
        self._event.wait()
        self._event.clear()
        self.myzwave.stop()
        return self.message
        
    def _cb(self, data):
        self.log.error("cb")
        if 'Info' in data:
            self.message.append(data['Info'])
            self._event.set()
        elif 'Find' in data:
            self._log.error("on entre dans le Find et on ajoute la data au message")
            self.message.append(data['Find'])
            self._log.error("event set")
            self._event.set()


MY_CLASS = {"cb" : zwave}

