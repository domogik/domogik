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

mir:ror by Violet support

Implements
==========

- MirrorManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.module import xPLModule
from domogik.xpl.lib.module import xPLResult
from domogik.xpl.lib.mirror import Mirror
from domogik.xpl.lib.queryconfig import Query

IS_DOMOGIK_MODULE = True
DOMOGIK_MODULE_DESCRIPTION = "Use Mir:ror device"


class MirrorManager(xPLModule):
    """ Manage the Mir:ror device and connect it to xPL
    """

    def __init__(self):
        """ Init module
        """
        xPLModule.__init__(self, name='mirror')
        # Get config
        #   - device
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('mirror', 'device', res)
        device = res.get_value()['device']
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('mirror', 'interval', res)
        interval = res.get_value()['interval']
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('mirror', 'nbmaxtry', res)
        nbmaxtry = res.get_value()['nbmaxtry']
        # Call Library
        self._mymirror  = Mirror(device, nbmaxtry, interval, \
                                 self._broadcastframe)
        self._mymirror.start()

    def _broadcastframe(self, action, ztamp_id):
        """ Send xPL message on network
            @param action : action done on mir:ror device
            @param ztamp_id : id of ztamp put on mir:ror
        """
        my_temp_message = XplMessage()
        my_temp_message.set_type("xpl-trig")
        my_temp_message.set_schema("sensor.basic")
        my_temp_message.add_data({"device" : "mirror"})
        my_temp_message.add_data({"type" : action})
        my_temp_message.add_data({"current" : ztamp_id})
        self._myxpl.send(my_temp_message)


if __name__ == "__main__":
    MirrorManager()
