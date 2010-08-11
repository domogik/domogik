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

IPX800 relay board management

Implements
==========

- IPXManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin, XplResult
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.ipx800 import IPXException
from domogik.xpl.lib.ipx800 import IPX
import threading


class IPXManager(XplPlugin):
    """ Implements a listener for IPX command messages 
        and launch background listening for relay board status
    """

    def __init__(self):
        """ Create lister and launch bg listening
        """
        XplPlugin.__init__(self, name = 'ipx800')

        # Configuration : list of IPX800
        self.ipx_list = {}
        num = 1
        loop = True
        while loop == True:
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-name' % str(num), res)
            name = res.get_value()['ipx-%s-name' % str(num)]
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-ip' % str(num), res)
            ip = res.get_value()['ipx-%s-ip' % str(num)]
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-int' % str(num), res)
            int = res.get_value()['ipx-%s-int' % str(num)]
            if name != "None":
                self._log.info("Configuration : name=%s, ip=%s, interval=%s" % (name, ip, int))
                self.ipx_list[name] = {"ip" : ip,
                                       "interval" : float(int)}
            else:
                loop = False
            num += 1

        ### Create IPX objects
        for ipx in self.ipx_list:
            self.ipx_list[ipx]['obj'] = IPX(self._log, self.send_xpl)
            try:
                self._log.info("Opening IPX800 named '%s' (ip : %s)" % (ipx, self.ipx_list[ipx]['ip']))
                self.ipx_list[ipx]['obj'].open(ipx, self.ipx_list[ipx]['ip'])
            except IPXException as e:
                self._log.error(e.value)
                print e.value
                self.force_leave()
                return

        ### Start listening each IPX800
        for ipx in self.ipx_list:
            try:
                self._log.info("Start listening to IPX800 named '%s'" % ipx)
                ipx_listen = threading.Thread(None,
                                              self.ipx_list[ipx]['obj'].listen,
                                              None,
                                              (self.ipx_list[ipx]['interval'],),
                                              {})
                ipx_listen.start()
            except IPXException as e:
                self._log.error(e.value)
                print e.value
                self.force_leave()
                return

        ### Create listeners for commands
        self._log.info("Creating listener for IPX 800")
        #Listener(self.ipx_command, self._myxpl, {'schema': 'control.basic',
        #        'xpltype': 'xpl-cmnd', 'type': ['output', 'count']})
        Listener(self.ipx_command, self._myxpl, {'schema': 'control.basic',
                'xpltype': 'xpl-cmnd', 'type': 'output'})

        self._log.info("Plugin ready :)")


    def send_xpl(self, device, current, type):
        # Send xpl-trig to give status change
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema('sensor.basic')
        msg.add_data({'device' :  device})
        msg.add_data({'type' :  type})
        msg.add_data({'current' :  current})
        self._myxpl.send(msg)


    def ipx_command(self, message):
        if 'device' in message.data:
            device = message.data['device']
        if 'type' in message.data:
            type = message.data['type'].lower()
        if 'current' in message.data:
            current = message.data['current'].upper()
 
        data = "device=%s, type=%s, current=%s" % (device, type, current)
        data_name = device.split("-")
        ipx_name = data_name[0]
        elt = data_name[1][0:-1]
        num = int(data_name[1][-1])

        if not ipx_name in self.ipx_list:
            self._log.warning("No IPX800 board called '%s' defined" % ipx_name)
            return

        # check data
        if elt == 'led' and current not in ['HIGH', 'LOW', 'PULSE'] \
           and type != 'output':
            self._log.warning("Bad data : %s" % data)
            return

        # TODO : other checks : counter
  
        # action in function of type
        if elt == 'led' and type == 'output' and current in ['HIGH', 'LOW']:
            self.ipx_list[ipx_name]['obj'].set_relay(num, current)
        elif elt == 'led' and type == 'output' and current== 'PULSE':
            self.ipx_list[ipx_name]['obj'].pulse_relay(num)

        # TODO : other actions : counter reset


if __name__ == "__main__":
    inst = IPXManager()

