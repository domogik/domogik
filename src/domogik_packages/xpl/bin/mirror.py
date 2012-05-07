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

mir:ror by Violet support

Implements
==========

- MirrorManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.mirror import Mirror
from domogik_packages.xpl.lib.mirror import MirrorException
import threading


class MirrorManager(XplPlugin):
    """ Manage the Mir:ror device and connect it to xPL
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='mirror')
        # Get config
        #   - device
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('mirror', 'device')

        # Init Mir:ror
        mirror  = Mirror(self.log, self.send_xpl)
        
        # Open Mir:ror
        try:
            mirror.open(device)
        except MirrorException as e:
            self.log.error(e.value)
            print(e.value)
            self.force_leave()
            return
            
        # Start reading Mir:ror
        mirror_process = threading.Thread(None,
                                   mirror.listen,
                                   "mirror-process-reader",
                                   (self.get_stop(),),
                                   {})
        self.register_thread(mirror_process)
        mirror_process.start()
        self.enable_hbeat()


    def send_xpl(self, device, type, current):
        """ Send xPL message on network
        """
        print("device:%s, type:%s, current:%s" % (device, type, current))
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema("sensor.basic")
        msg.add_data({"device" : device})
        msg.add_data({"type" : type})
        msg.add_data({"current" : current})
        self.myxpl.send(msg)


if __name__ == "__main__":
    MirrorManager()
