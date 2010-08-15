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

from domogik.xpl.common.xplconnector import Listener, XplTimer
from domogik.xpl.common.plugin import XplPlugin, XplResult
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.plcbus import PLCBUSAPI
from domogik.xpl.common.queryconfig import Query
import threading
import time

class PlcBusMain(XplPlugin):
    ''' Manage PLCBus technology, send and receive order/state
    '''

    def __init__(self):
        '''
        Create the plcbusMain class
        This class is used to connect PLCBUS to the xPL Network
        '''
        # Load config
        XplPlugin.__init__(self, name = 'plcbus')
        self._config = Query(self._myxpl)
        # Create listeners
        Listener(self._plcbus_cmnd_cb, self._myxpl, {
            'schema': 'plcbus.basic',
            'xpltype': 'xpl-cmnd',
        })
        res = XplResult()
        self._config.query('plcbus', 'device', res)
        device = res.get_value()['device']
        res = XplResult()
        self._config.query('plcbus', 'usercode', res)
        self._usercode = res.get_value()['usercode']
        res = XplResult()
        self._config.query('plcbus', 'probe-interval', res)
        self._probe_inter = int(res.get_value()['probe-interval'])
        res = XplResult()
        self._config.query('plcbus', 'probe-list', res)
        self._probe_list = res.get_value()['probe-list']

        # Create log instance
        self._log = self.get_my_logger()
        self.api = PLCBUSAPI(self._log, device, self._command_cb, self._message_cb)
        if self._probe_inter != 0:
            self._probe_status = {}
            self._probe_stop = threading.Event()
            self._probe_thr = XplTimer(self._probe_inter, self._send_probe, self._probe_stop, self._myxpl)
            self._probe_thr.start()
            self.register_timer(self._probe_thr)

    def _send_probe(self):
        """ Send probe message 

        """
        for h in self._probe_list:
            self.api.send("GET_ALL_ID_PULSE", h, self._usercode, 0, 0)
            time.sleep(1)
            self.api.send("GET_ALL_ON_ID_PULSE", h, self._usercode, 0, 0)
            time.sleep(1)

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
            dev = message.data['device'].upper()
        if 'usercode' in message.data:
            user = message.data['usercode']
        else:
            user = self._usercode
        if 'data1' in message.data:
            level = message.data['data1']
        if 'data2' in message.data:
            rate = message.data['data2']
        self._log.debug("%s received : device = %s, user code = %s, level = "\
                "%s, rate = %s" % (cmd.upper(), dev, user, level, rate))
#        if cmd == 'GET_ALL_ON_ID_PULSE':
#            self.api.get_all_on_id(user, dev)
#        else:
        self.api.send(cmd.upper(), dev, user, level, rate)

    def _command_cb(self, f):
        ''' Called by the plcbus library when a command has been sent.
        If the commands need an ack, this callback will be called only after the ACK has been received
        @param : plcbus frame as an array
        '''
        if f["d_command"] == "GET_ALL_ID_PULSE":
            data = int("%s%s" % (f["d_data1"], f["d_data2"]), 16)
            house = f["d_home_unit"][0]
            for i in range(0,16):
                unit = data >> i & 1
                code = "%s%s" % (house, i+1)
                if unit and not code in self._probe_status:
                    self._probe_status[code] = ""
                    self._log.info("New device discovered : %s" % code)
                elif (not unit) and code in self._probe_status:
                    del self._probe_status[code]
        elif f["d_command"] == "GET_ALL_ON_ID_PULSE":
            data = int("%s%s" % (f["d_data1"], f["d_data2"]), 16)
            house = f["d_home_unit"][0]
            for i in range(0,16):
                unit = data >> i & 1
                code = "%s%s" % (house, i+1)
                if code in self._probe_status and (self._probe_status[code] != str(unit)):
                    self._probe_status[code] = str(unit)
                    if unit == 1:
                        command = "ON"
                    else:
                        command ="OFF"
                    mess = XplMessage()
                    mess.set_type('xpl-trig')
                    mess.set_schema('plcbus.basic')
                    mess.add_data({"usercode" : f["d_user_code"], "device": code,
                                   "command": command})
                    self._myxpl.send(mess)
        else:
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

