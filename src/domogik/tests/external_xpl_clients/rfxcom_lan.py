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

Test

Implements
==========

- Test

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin

import threading
import traceback


class Test(XplPlugin):
    """ Test
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='test', test = True, source='rfxcom-lan.0004a31bb6ac')

        self.send_xpl(schema = "sensor.basic", data = {"current" : 13, "address" : "foo", "type" : "temp"})
        #self.ready()


    def send_xpl(self, message = None, schema = None, data = {}):
        """ Send xPL message on network
        """
        if message != None:
            self.log.debug(u"send_xpl : send full message : {0}".format(message))
            self.myxpl.send(message)

        else:
            self.log.debug(u"send_xpl : Send xPL message xpl-trig : schema:{0}, data:{1}".format(schema, data))
            msg = XplMessage()
            msg.set_type("xpl-trig")
            msg.set_schema(schema)
            for key in data:
                msg.add_data({key : data[key]})
            self.myxpl.send(msg)


if __name__ == "__main__":
    Test()
