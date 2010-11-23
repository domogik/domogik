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
            self._config = Query(self.myxpl, self.log)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-login' % str(num), res)
            login = res.get_value()['ipx-%s-login' % str(num)]
            if login == "None":
                login = None
            self._config = Query(self.myxpl, self.log)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-password' % str(num), res)
            password = res.get_value()['ipx-%s-password' % str(num)]
            self._config = Query(self.myxpl, self.log)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-name' % str(num), res)
            name = res.get_value()['ipx-%s-name' % str(num)]
            self._config = Query(self.myxpl, self.log)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-ip' % str(num), res)
            address = res.get_value()['ipx-%s-ip' % str(num)]
            self._config = Query(self.myxpl, self.log)
            res = XplResult()
            self._config.query('ipx800', 'ipx-%s-int' % str(num), res)
            inter = res.get_value()['ipx-%s-int' % str(num)]
            if name != "None":
                self.log.info("Configuration : login=%s, password=***, name=%s, ip=%s, interval=%s" % 
                               (login, name, address, inter))
                self.ipx_list[name] = {"login" : login,
                                       "password" : password,
                                       "ip" : address,
                                       "interval" : float(inter)}
            else:
                loop = False
            num += 1

        ### Create IPX objects
        for ipx in self.ipx_list:
            self.ipx_list[ipx]['obj'] = IPX(self.log, self.send_xpl)
            try:
                self.log.info("Opening IPX800 named '%s' (ip : %s)" % 
                               (ipx, self.ipx_list[ipx]['ip']))
                self.ipx_list[ipx]['obj'].open(ipx, self.ipx_list[ipx]['ip'],
                                               self.ipx_list[ipx]['login'],
                                               self.ipx_list[ipx]['password'])
            except IPXException as err:
                self.log.error(err.value)
                print err.value
                self.force_leave()
                return

        ### Start listening each IPX800
        for ipx in self.ipx_list:
            try:
                self.log.info("Start listening to IPX800 named '%s'" % ipx)
                ipx_listen = threading.Thread(None,
                                              self.ipx_list[ipx]['obj'].listen,
                                              None,
                                              (self.ipx_list[ipx]['interval'],),
                                              {})
                ipx_listen.start()
            except IPXException as err:
                self.log.error(err.value)
                print err.value
                self.force_leave()
                return

        ### Create listeners for commands
        self.log.info("Creating listener for IPX 800")
        #Listener(self.ipx_command, self.myxpl, {'schema': 'control.basic',
        #        'xpltype': 'xpl-cmnd', 'type': ['output', 'count']})
        Listener(self.ipx_command, self.myxpl, {'schema': 'control.basic',
                'xpltype': 'xpl-cmnd', 'type': 'output'})

        self.enable_hbeat()
        self.log.info("Plugin ready :)")


    def send_xpl(self, msg_device, msg_current, msg_type):
        """ Send xpl-trig to give status change
            @param msg_device : device
            @param msg_current : device's value
            @param msg_type : device's type
        """
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema('sensor.basic')
        msg.add_data({'device' :  msg_device})
        msg.add_data({'type' :  msg_type})
        msg.add_data({'current' :  msg_current})
        self.myxpl.send(msg)


    def ipx_command(self, message):
        """ Call ipx800 lib function in function of given xpl message
            @param message : xpl message
        """
        if 'device' in message.data:
            msg_device = message.data['device']
        if 'type' in message.data:
            msg_type = message.data['type'].lower()
        if 'current' in message.data:
            msg_current = message.data['current'].upper()
 
        data = "device=%s, type=%s, current=%s" % (msg_device, msg_type, msg_current)
        data_name = msg_device.split("-")
        ipx_name = data_name[0]
        elt = data_name[1][0:-1]
        num = int(data_name[1][-1])

        if not ipx_name in self.ipx_list:
            self.log.warning("No IPX800 board called '%s' defined" % ipx_name)
            return

        # check data
        if elt == 'led' and msg_current not in ['HIGH', 'LOW', 'PULSE'] \
           and msg_type != 'output':
            self.log.warning("Bad data : %s" % data)
            return

        # TODO in a next release : other checks : counter
  
        # action in function of type
        if elt == 'led' and msg_type == 'output' and msg_current in ['HIGH', 'LOW']:
            self.ipx_list[ipx_name]['obj'].set_relay(num, msg_current)
        elif elt == 'led' and msg_type == 'output' and msg_current == 'PULSE':
            self.ipx_list[ipx_name]['obj'].pulse_relay(num)

        # TODO in a next release : other actions : counter reset


if __name__ == "__main__":
    INST = IPXManager()

