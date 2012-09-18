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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.ipx800 import IPXException
from domogik_packages.xpl.lib.ipx800 import IPX
import threading
import traceback


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
        self._config = Query(self.myxpl, self.log)
        while loop == True:
            model = self._config.query('ipx800', 'model-%s' % str(num))
            login = self._config.query('ipx800', 'login-%s' % str(num))
            password = self._config.query('ipx800', 'password-%s' % str(num))
            name = self._config.query('ipx800', 'name-%s' % str(num))
            address = self._config.query('ipx800', 'ip-%s' % str(num))
            inter = self._config.query('ipx800', 'int-%s' % str(num))
            if name != None:
                self.log.info("Configuration : login=%s, password=***, name=%s, ip=%s, interval=%s" % 
                               (login, name, address, inter))
                self.ipx_list[name] = {"login" : login,
                                       "password" : password,
                                       "model" : model,
                                       "ip" : address,
                                       "interval" : float(inter)}
                num += 1
            else:
                loop = False

        # no ipx configured
        if num == 1:
            msg = "No ipx800 board configured. Exiting plugin"
            self.log.info(msg)
            print(msg)
            self.force_leave()
            return

        ### Create IPX objects
        num_ok = 0
        for ipx in self.ipx_list:
            self.ipx_list[ipx]['obj'] = IPX(self.log, self.send_xpl, self.get_stop())
            try:
                self.log.info("Opening IPX800 named '%s' (ip : %s)" % 
                               (ipx, self.ipx_list[ipx]['ip']))
                self.ipx_list[ipx]['obj'].open(ipx, self.ipx_list[ipx]['ip'],
                                               self.ipx_list[ipx]['model'],
                                               self.ipx_list[ipx]['login'],
                                               self.ipx_list[ipx]['password'])
            except:
                self.log.error("Error opening board '%s' : %s " % (ipx, traceback.format_exc()))
                print("Error opening board '%s' : check logs" % ipx)
            else:
                num_ok += 1

        # no valid ipx800 board detected
        if num_ok == 0:
            msg = "No valid IPX800 board configured. Exiting plugin..."
            self.log.info(msg)
            print(msg)
            self.force_leave()
            return

        ### Start listening each IPX800
        for ipx in self.ipx_list:
            try:
                self.log.info("Start listening to IPX800 named '%s'" % ipx)
                ipx_listen = threading.Thread(None,
                                              self.ipx_list[ipx]['obj'].listen,
                                              "listen_ipx",
                                              (self.ipx_list[ipx]['interval'],),
                                              {})
                ipx_listen.start()
            except IPXException as err:
                self.log.error(err.value)
                print(err.value)
                # we don't quit plugin if an error occured
                # we can loose a board for a little time
                #self.force_leave()
                #return

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
        if msg_type != None:
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
            msg_current = message.data['current'].lower()
 
        data = "device=%s, type=%s, current=%s" % (msg_device, msg_type, msg_current)
        print data
        data_name = msg_device.split("-")
        ipx_name = data_name[0]
        elt = data_name[1][0:-1]
        num = int(data_name[1][-1])

        if not ipx_name in self.ipx_list:
            self.log.warning("No IPX800 board called '%s' defined" % ipx_name)
            return

        # check data
        if elt == 'led' and msg_current not in ['high', 'low', 'pulse'] \
           and msg_type != 'output':
            self.log.warning("Bad data : %s" % data)
            return

        # TODO in a next release : other checks : counter
  
        # action in function of type
        if elt == 'led' and msg_type == 'output' and msg_current in ['high', 'low']:
            self.ipx_list[ipx_name]['obj'].set_relay(num, msg_current)
        elif elt == 'led' and msg_type == 'output' and msg_current == 'pulse':
            self.ipx_list[ipx_name]['obj'].pulse_relay(num)

        # TODO in a next release : other actions : counter reset


if __name__ == "__main__":
    INST = IPXManager()

