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

Samsung televisions manager

Implements
==========

- SamsungTVManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.tv_samsg import SamsungTV, SamsungTVException


class SamsungTVManager(XplPlugin):
    """ Manage Samsung televisions
    """

    def __init__(self):
        """ Init manager
        """
        XplPlugin.__init__(self, name = 'tv_samsg')

        # Configuration : list of televisions
        self.televisions = {}
        num = 1
        loop = True
        self._config = Query(self.myxpl, self.log)
        while loop == True:
            name = self._config.query('tv_samsg', 'tv-%s-name' % str(num))
            device = self._config.query('tv_samsg', 'tv-%s-device' % str(num))
            if name != None:
                self.log.info("Configuration : name=%s, device=%s" % (name, device))
                self.televisions[name] = {"device" : device}
            else:
                loop = False
            num += 1

        ### Create SamsungTV objects
        for television in self.televisions:
            self.televisions[television]['obj'] = SamsungTV(self.log)
            try:
                self.log.info("Opening Samsung Television named '%s' (device : %s)" %
                               (television, self.televisions[television]['device']))
                self.televisions[television]['obj'].open(self.televisions[television]['device'])
            except SamsungTVException as err:
                self.log.error(err.value)
                print(err.value)
                self.force_leave()
                return

        # Create listener
        Listener(self.television_cb, self.myxpl, {'schema': 'control.basic',
                'xpltype': 'xpl-cmnd', 'type': 'television'})
        self.log.debug("Listener for tv_samsg created")

        self.enable_hbeat()

    def television_cb(self, message):
        """ Call tv_samsg lib
            @param message : xPL message detected by listener
        """
        # device contains name of television which will be used to get device
        if 'device' in message.data:
            name = message.data['device']
        if 'current' in message.data:
            command = message.data['current']
        else:
            self._log.warning("Xpl message : missing 'current' attribute")
            return
        if 'data1' in message.data:
            data1 = int(message.data['data1'])
        else:
            data1 = None

        try:
            device = self.televisions[name]["device"]
        except KeyError:
            self.log.warning("Television named '%s' is not defined" % name)
            return
        
        self.log.info("Television command received for '%s' on '%s'" % (name, device))
        status = self.televisions[name]['obj'].send(command, data1)

        # Send xpl-trig to say plugin receive command
        print("S=%s" % status)
        if status == True:
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('sensor.basic')
            mess.add_data({'device' :  device})
            mess.add_data({'type' :  'television'})
            mess.add_data({'current' :  command})
            if data1 != None:
                mess.add_data({'data1' :  data1})
            print(mess)
            self.myxpl.send(mess)


if __name__ == "__main__":
    inst = SamsungTVManager()

