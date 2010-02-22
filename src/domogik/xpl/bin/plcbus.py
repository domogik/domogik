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

Module purpose
==============

xPL PLCBUS client

Implements
==========

- plcbusMain.__init__(self)
- plcbusMain.plcbus_cmnd_cb(self, message)
- plcbusMain.plcbus_send_ack(self, message)

@author: François PINET <domopyx@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.lib.xplconnector import Listener
from domogik.xpl.lib.module import xPLModule, xPLResult
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.plcbus import PLCBUSAPI
from domogik.xpl.lib.queryconfig import Query

IS_DOMOGIK_MODULE = True
DOMOGIK_MODULE_DESCRIPTION = "Manage Plcbus devices"


class PlcBusMain(xPLModule):
    ''' Manage PLCBus technology, send and receive order/state
    '''

    def __init__(self):
        '''
        Create the plcbusMain class
        This class is used to connect PLCBUS to the xPL Network
        '''
        # Load config
        xPLModule.__init__(self, name = 'plcbus')
        self._config = Query(self._myxpl)
        # Create listeners
        Listener(self._plcbus_cmnd_cb, self._myxpl, {
            'schema': 'control.basic',
            'xpltype': 'xpl-cmnd',
        })
        res = xPLResult()
        self._config.query('plcbus', 'device', res)
        device = res.get_value()['device']
        self.api = PLCBUSAPI(device) #TODO :need to be updated with dynamic config
        # Create log instance
        self._log = self.get_my_logger()

    def _plcbus_cmnd_cb(self, message):
        '''
        General callback for all command messages
        '''
        cmd = None
        dev = None
        user = None
        level = 0
        rate = 0
        if message.has_key('command'):
            cmd = message.data['command']
        if message.has_key('device'):
            dev = message.data['device']
        if message.has_key('usercode'):
            user = message.data['usercode']
        if message.has_key('level'):
            level = message.data['level']
        if message.has_key('rate'):
            rate = message.data['rate']
        self._log.debug("%s received : device = %s, user code = %s, level = "\
                "%s, rate = %s" % (cmd.upper(), dev, user, level, rate))
        if cmd == 'GET_ALL_ON_ID_PULSE':
            self.api.get_all_on_id(dev, user)
        else:
            self.api.send(cmd.upper(), dev, user, level, rate)

if __name__ == "__main__":
    PlcBusMain()
