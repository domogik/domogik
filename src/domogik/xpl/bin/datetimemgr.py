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

Send time informations on the network

Implements
==========

- xPLDateTime.__init__(self)
- xPLDateTime._format(self, nb)
- xPLDateTime._send_datetime(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from time import localtime
from domogik.xpl.common.xplconnector import xPLTimer
from domogik.xpl.common.module import xPLModule
from domogik.xpl.common.xplmessage import XplMessage


IS_DOMOGIK_PLUGIN = True
DOMOGIK_PLUGIN_DESCRIPTION = "Send date and time on the xPL network every minute"
DOMOGIK_PLUGIN_CONFIGURATION=[
      {"id" : 0,
       "key" : "startup-module",
       "description" : "Automatically start module at Domogik startup",
       "default" : "False"},
      ]
class XPLDateTime(xPLModule):
    '''
    Send date and time on the xPL network every minute
    '''

    def __init__(self):
        xPLModule.__init__(self, name = 'ldtmgr')
        
        self._timer = xPLTimer(10, self._send_datetime, self.get_stop())
        self.register_timer(self._timer)
        self._timer.start()

    def _format(self, number):
        '''
        Format the number
        '''
        if int(number) < 10:
            return "0%s" % number
        else:
            return number

    def _send_datetime(self):
        '''
        Send date and time on xPL network
        '''
        ldt = localtime()
        date = "%s%s%s" % (ldt[0], self._format(ldt[1]), self._format(ldt[2]))
        time = "%s%s%s" % (self._format(ldt[3]), self._format(ldt[4]), self._format(ldt[5]))
        datetime = "%s%s" % (date, time)
        datetimedaynumber = "%s%s" % (datetime, ldt[6])
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("datetime.basic")
        mess.add_data({"date" :  date})
        mess.add_data({"time" :  time})
        mess.add_data({"datetime" :  datetime})
        mess.add_data({"format1" :  datetimedaynumber})
        self._myxpl.send(mess)

if __name__ == "__main__":
    XPLDateTime()
