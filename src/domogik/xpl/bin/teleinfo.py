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
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.lib.teleinfo import Teleinfo
from domogik.xpl.lib.teleinfo import TeleinfoException
from domogik.xpl.common.queryconfig import Query
import threading
import re


class TeleinfoManager(XplPlugin):
    '''
    Manage the Téléinfo stuff and connect it to xPL
    '''

    def __init__(self):
        '''
        Start teleinfo device handler
        '''
        XplPlugin.__init__(self, name='teleinfo')
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('teleinfo', 'device')
        interval = self._config.query('teleinfo', 'interval')

        # Init Teleinfo
        teleinfo  = Teleinfo(self.log, self.send_xpl)
        
        # Open Teleinfo modem
        try:
            teleinfo.open(device)
        except TeleinfoException as err:
            self.log.error(err.value)
            print err.value
            self.force_leave()
            return
            
        self.add_stop_cb(teleinfo.close)
        # Start reading Teleinfo
        teleinfo_process = threading.Thread(None,
                                   teleinfo.listen,
                                   'teleinfo-listen',
                                   (float(interval),),
                                   {})                                  
        teleinfo_process.start()                              
        self.enable_hbeat()

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

        try:
            for entry in frame:
                key = re.sub('[^w\.]','',entry["name"].lower())
                val = re.sub('[^w\.]','',entry["value"].lower())
                my_temp_message.add_data({ key : val })
            my_temp_message.add_data({"device": "teleinfo"})
        except :
            self.log.warn("Message ignored : %s" % my_temp_message)

        try:
            self.myxpl.send(my_temp_message)
        except XplMessageError:
            #We ignore the message if some values are not correct because it can happen with teleinfo ...
            pass

if __name__ == "__main__":
    TeleinfoManager()
