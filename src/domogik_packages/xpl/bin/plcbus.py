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

@author: Francois PINET <domopyx@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener, XplTimer
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik_packages.xpl.lib.plcbus import PLCBUSAPI
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
        # Create listeners
        Listener(self._plcbus_cmnd_cb, self.myxpl, {
            'schema': 'plcbus.basic',
            'xpltype': 'xpl-cmnd',
        })
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('plcbus', 'device')
        self._usercode = self._config.query('plcbus', 'usercode')
        self._probe_inter = int( self._config.query('plcbus', 'probe-interval'))
        self._probe_list = self._config.query('plcbus', 'probe-list')

        # Create log instance
        self.api = PLCBUSAPI(self.log, device, self._command_cb, self._message_cb)
        self.add_stop_cb(self.api.stop)
        if self._probe_inter == 0:
            self.log.warning("The probe interval has been set to 0. This is not correct. The plugin will use a probe interval of 5 seconds")
            self._probe_inter = 5 
        self._probe_status = {}
        self._probe_thr = XplTimer(self._probe_inter, self._send_probe, self.myxpl)
        self._probe_thr.start()
#       self.register_timer(self._probe_thr)
        self.enable_hbeat()

    def _send_probe(self):
        """ Send probe message 

        """
        for h in self._probe_list:
            self.log.debug("send get_all_id")
            self.api.send("GET_ALL_ID_PULSE", h, self._usercode, 0, 0)
            time.sleep(1)
            self.log.debug("send get_all_on_id")
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
        self.log.debug("%s received : device = %s, user code = %s, level = "\
                "%s, rate = %s" % (cmd.upper(), dev, user, level, rate))
#        if cmd == 'GET_ALL_ON_ID_PULSE':
#            self.api.get_all_on_id(user, dev)
#        else:
        self.api.send(cmd.upper(), dev, user, level, rate)
#       Workaround to send an ON command when dimmer = 0
        if cmd == 'PRESET_DIM' and level == 0:
            print("cmd : %s " % cmd)
            print("level : %s " % level)     
            self.api.send("OFF", dev, user)

        if cmd == 'PRESET_DIM' and level != 0:
            print('WORKAROUD : on fait suivre le DIM d un ON pour garder les widgets switch allumes')
            print("DEBUG cmd : %s " % cmd)
            print("DEBUG level : %s " % level)
            self.api.send("ON", dev, user)


    def _command_cb(self, f):
        ''' Called by the plcbus library when a command has been sent.
        If the commands need an ack, this callback will be called only after the ACK has been received
        @param : plcbus frame as an array
        '''
        if f["d_command"] == "GET_ALL_ID_PULSE":
            data = int("%s%s" % (f["d_data1"], f["d_data2"]))
            house = f["d_home_unit"][0]
            for i in range(0,16):
                unit = data >> i & 1
                code = "%s%s" % (house, i+1)
                if unit and not code in self._probe_status:
                    self._probe_status[code] = ""
                    self.log.info("New device discovered : %s" % code)
                elif (not unit) and code in self._probe_status:
                    del self._probe_status[code]
        elif f["d_command"] == "GET_ALL_ON_ID_PULSE":
            data = "%s%s" % (bin(f["d_data1"])[2:].zfill(8), bin(f["d_data2"])[2:].zfill(8))
            print("f : %s" % f)
            print("data : %s" % data)
            house = f["d_home_unit"][0]
            item = 16
            for c in data:
                unit=int(c)
                code = "%s%s" % (house, item)
                print("Etat : %s " % code, unit)
                if code in self._probe_status and (self._probe_status[code] != str(unit)):
                    print('DEBUG in rentre dans le IF detection GET_ALL_ON')
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
                    self.myxpl.send(mess)
                item = item - 1
        else:
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('plcbus.basic')
            mess.add_data({"usercode" : f["d_user_code"], "device": f["d_home_unit"],
                           "command": f["d_command"], "data1": f["d_data1"], "data2": f["d_data2"]})
            self.myxpl.send(mess)

#           Workaround to for switch widget go ON when dimmer is send
#        if f["d_command"] == 'PRESET_DIM' and f["d_data1"] != 0 : 
#            print('WORKAROUD : on fait suivre le DIM d un ON pour garder les widgets switch allumes')
            #print("data1 : %s " % f["d_data1"])
#            mess = XplMessage()
#            mess.set_type('xpl-stat')
#            mess.set_schema('plcbus.basic')
#            mess.add_data({"usercode" : f["d_user_code"], "device": f["d_home_unit"], "command": 'ON'})
#            self.myxpl.send(mess)

    def _message_cb(self, message):
        print("Message : %s " % message)

if __name__ == "__main__":
    PlcBusMain()

