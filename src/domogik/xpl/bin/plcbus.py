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

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import xPLPlugin, xPLResult
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.plcbus import PLCBUSAPI
from domogik.xpl.common.queryconfig import Query

IS_DOMOGIK_PLUGIN = True
DOMOGIK_PLUGIN_TECHNOLOGY = "PLCBus"
DOMOGIK_PLUGIN_DESCRIPTION = "Manage Plcbus devices"
DOMOGIK_PLUGIN_CONFIGURATION=[
      {"id" : 0,
       "key" : "startup-plugin",
       "description" : "Automatically start plugin at Domogik startup",
       "default" : "False"},
      {"id" : 1,
       "key" : "device",
       "description" : "Plcbus device (ex : TODO )",
       "default" : "/dev/ttyUSB0"}]



class PlcBusMain(xPLPlugin):
    ''' Manage PLCBus technology, send and receive order/state
    '''

    def __init__(self):
        '''
        Create the plcbusMain class
        This class is used to connect PLCBUS to the xPL Network
        '''
        # Load config
        xPLPlugin.__init__(self, name = 'plcbus')
        self._config = Query(self._myxpl)
        # Create listeners
        Listener(self._plcbus_cmnd_cb, self._myxpl, {
            'schema': 'plcbus.basic',
            'xpltype': 'xpl-cmnd',
        })
        res = xPLResult()
        self._config.query('plcbus', 'device', res)
        device = res.get_value()['device']
        self.api = PLCBUSAPI(device, self._command_cb, self._message_cb) 
        # Create log instance
        self._log = self.get_my_logger()

    def _plcbus_cmnd_cb(self, message):
        '''
        General callback for all command messages
        '''
        cmd = None
        dev = None
        user = '00'
        level = 0
        rate = 0
        if 'command' in message.data:
            cmd = message.data['command']
        if 'device' in message.data:
            dev = message.data['device']
        if 'usercode' in message.data:
            user = message.data['usercode']
        if 'data1' in message.data:
            level = message.data['data1']
        if 'data2' in message.data:
            rate = message.data['data2']
        self._log.debug("%s received : device = %s, user code = %s, level = "\
                "%s, rate = %s" % (cmd.upper(), dev, user, level, rate))
        if cmd == 'GET_ALL_ON_ID_PULSE':
            self.api.get_all_on_id(user, dev)
        else:
            self.api.send(cmd.upper(), dev, user, level, rate)

    def _command_cb(self, f):
        ''' Called by the plcbus library when a command has been sent.
        If the commands need an ack, this callback will be called only after the ACK has been received
        @param : plcbus frame as an array
        '''
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('plcbus.basic')
        mess.add_data({"usercode" : f["d_user_code"], "device": f["d_home_unit"],
            "command": f["d_command"], "data1": f["d_data1"], "data2": f["d_data2"]})
        self._myxpl.send(mess) 

    def _message_cb(self, message):
        print "Message : %s " % message

if __name__ == "__main__":
    PlcBusMain()
