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

TODO

Implements
==========

TODO

@author: Fritz <fritz.smh@gmail.com>, BTS Project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.xplconnector import Listener
import re


class BtsGeneral(XplPlugin):
    """ BTS : general scenario
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='bts_gen')

        # Get config for input
        self._config = Query(self.myxpl, self.log)
        input = self._config.query('bts_gen', 'input')

        # Get config for outputs
        self.outputs = {}
        num = 1
        loop = True
        while loop == True:
            output = self._config.query('bts_gen', 'output-%s' % str(num))
            level = self._config.query('bts_gen', 'level-%s' % str(num))
            if output != None:
                self.log.info("Configuration : output=%s, level=%s" % (output, level))
                self.outputs[output] = level
            else:
                loop = False
            num += 1

        ### Define listener for ipx800 input
        Listener(self.action, 
                 self.myxpl, 
                 {'schema': 'sensor.basic',
                  'xpltype': 'xpl-trig',
                  'type': 'input',
                  'device' : input})

       
    def action(self, message):
        """ action on input change

            TODO : explain here what is done 

            @param message : xpl message
        """
        print("Input change : make action...")
        # Get input status
        input_level = message.data['current']

        # If input is HIGH
        if input_level == "HIGH":
            for address in self.outputs:
                self.set_ipx800_relay(address, self.outputs[address])
        # If input is LOW, we send opposite values
        else:
            for address in self.outputs:
                level = self.outputs[address]
                if level.upper() == "HIGH":
                    level = "LOW"
                else:
                    level = "HIGH"
                self.set_ipx800_relay(address, level)

    def set_ipx800_relay(self, address, level):
        """ set an ipx800 relay level at HIGH/LOW
            @param addres : ipx800 relay address
            @param level : HIGH/LOW
        """
        print("Set '%s' to '%s'" % (address, level))
        msg = XplMessage()
        msg.set_type("xpl-cmnd")
        msg.set_schema('control.basic')
        msg.add_data({'device' :  address})
        msg.add_data({'type' :  'output'})
        msg.add_data({'current' :  level})
        self.myxpl.send(msg)



if __name__ == "__main__":
    BtsGeneral()
