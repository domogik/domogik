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

xPL Téléinfo client

Implements
==========

- Teleinfo

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin, XplResult
from domogik.xpl.lib.teleinfo import Teleinfo
from domogik.xpl.lib.teleinfo import TeleinfoException
from domogik.xpl.common.queryconfig import Query
import threading


class TeleinfoManager(XplPlugin):
    '''
    Manage the Téléinfo stuff and connect it to xPL
    '''

    def __init__(self):
        '''
        Start teleinfo device handler
        '''
        XplPlugin.__init__(self, name='teleinfo')
        self._config = Query(self._myxpl)
        res = XplResult()
        self._config.query('teleinfo', 'device', res)
        device = res.get_value()['device']
        res = XplResult()
        self._config.query('teleinfo', 'interval', res)
        interval = res.get_value()['interval']

        # Init Teleinfo
        teleinfo  = Teleinfo(self._log, self.send_xpl)
        
        # Open Teleinfo modem
        try:
            teleinfo.open(device)
        except TeleinfoException as err:
            self._log.error(err.value)
            print err.value
            self.force_leave()
            return
            
        # Start reading Teleinfo
        teleinfo_process = threading.Thread(None,
                                   teleinfo.listen,
                                   None,
                                   (float(interval),),
                                   {})                                  
        teleinfo_process.start()                              

    def send_xpl(self, frame):
        ''' Send a frame from teleinfo device to xpl
        @param frame : a dictionnary mapping teleinfo informations
        '''
        my_temp_message = XplMessage()
        my_temp_message.set_type("xpl-stat")
        if "ADIR1" in frame:
            my_temp_message.set_schema("teleinfo.short")
        else:
            my_temp_message.set_schema("teleinfo.basic")

        for entry in frame:
            my_temp_message.add_data({entry["name"].lower() : entry["value"]})
        my_temp_message.add_data({"device": "teleinfo"})

        self._myxpl.send(my_temp_message)

if __name__ == "__main__":
    TeleinfoManager()
