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

RelayBoard USB manager

Implements
==========

- RelayBoardUSBmanager based on Samsung TV Manager from Fritz <fritz.smh@gmail.com> for  Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.gceusbrb import Relayboardusb, RelayboardusbException
import traceback
import threading

class RelayBoardUSBmanager(XplPlugin):
    """ Manage USB Relay Board
    """

    def __init__(self):
        """ Init manager
        """
        XplPlugin.__init__(self, name = 'gceusbrb')

        # Configuration : list of relayboard
        self.relayboards = {}
        num = 1
        loop = True
        self._config = Query(self.myxpl, self.log)
        while loop == True:
            name = self._config.query('gceusbrb', 'rb-%s-name' % str(num))
            device = self._config.query('gceusbrb', 'rb-%s-device' % str(num))
            if name != None:
                self.log.info("Configuration : name=%s, device=%s" % (name, device))
                self.relayboards[name] = {"device" : device}
            else:
                loop = False
            num += 1

        ### Create Relayboardusb objects ex.SamsungTV
        for relayboard in self.relayboards:
            self.relayboards[relayboard]['obj'] = Relayboardusb(self.log,self.send_xpl)
            try:
                self.log.info("Opening RelayBoard named '%s' (device : %s)" %
                               (relayboard, self.relayboards[relayboard]['device']))
                self.relayboards[relayboard]['obj'].open(self.relayboards[relayboard]['device'],relayboard)
            except RelayboardusbException as err:
                self.log.error(err.value)
                print err.value
                self.force_leave()
                return

        # Create listener
        Listener(self.relayboard_cb, self.myxpl, {'schema': 'control.basic','xpltype': 'xpl-cmnd', 'type': 'output'})
        self.log.debug("Listener for gceusbrb created")

        self.enable_hbeat()
        self.log.info("RB Plugin ready :)")

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

    def relayboard_cb(self, message):
        """ Call gceusbrb lib
            @param message : xPL message detected by listener
        """
        # device contains name of relayboard which will be used to get device
        if 'device' in message.data:
            msg_device = message.data['device']
        if 'type' in message.data:
            msg_type = message.data['type'].lower()
        if 'current' in message.data:
            msg_current = message.data['current'].upper()

        data = "device=%s, type=%s, current=%s" % (msg_device, msg_type, msg_current)
        data_name = msg_device.split("-")
        rb_name = data_name[0]
        elt = data_name[1][0:-1]
        num = int(data_name[1][-1])

        self.log.info("RelayBoard command received for '%s' on '%s'" % (rb_name, msg_device))

        if not rb_name in self.relayboards:
           self.log.warning("No Relay board called '%s' defined" % rb_name)
           return

        # check data
        if elt == 'led' and msg_current not in ['HIGH', 'LOW'] and msg_type != 'output':
            self.log.warning("Bad data : %s" % data)
            return
        
        # action in function of type
        self.relayboards[rb_name]['obj'].set_relay(num, msg_current)
        # TODO in a next release : pulse_relay ?

if __name__ == "__main__":
    inst = RelayBoardUSBmanager()


