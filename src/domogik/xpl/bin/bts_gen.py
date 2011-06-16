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

        # initial state to off
        self.state = "off"

        # Get config for input
        self._config = Query(self.myxpl, self.log)
        input = self._config.query('bts_gen', 'input')
        self.threshold = self._config.query('bts_gen', 'threshold')

        # Get config for outputs
        self.outputs = {}
        num = 1
        loop = True
        while loop == True:
            output = self._config.query('bts_gen', 'output-%s' % str(num))
            level = self._config.query('bts_gen', 'level-%s' % str(num))
            if level == "True":
                level = "HIGH"
            else:
                level = "LOW"
            if output != None:
                msg = "Configuration : output=%s, level=%s" % (output, level)
                self.log.info(msg)
                print msg
                type, address = self.explode(output)
                self.outputs[output] = {"level" : level,
                                        "type" : type,
                                        "address" : address}
            else:
                loop = False
            num += 1

        # Display scenario state (on/off)
        msg = "Scenario is %s" % self.state
        self.log.debug(msg)
        print(msg)

        ### check input type
        # input is "foo:bar" format. foo = type, bar = address
        # example : ipx800:ipx-btn3
        type, address = self.explode(input)

        # x10 can't be used as input : a physical button action can't be seen
        # by x10 plugin, so there won't be any xpl-trig message

        if type == "ipx800":
            msg = "Input type : ipx800"
            print(msg)
            self.log.info(msg)

            ### Define listener for ipx800 input
            Listener(self.action_ipx800, 
                     self.myxpl, 
                     {'schema': 'sensor.basic',
                      'xpltype': 'xpl-trig',
                      'type': 'input',
                      'device' : input})

        if type == "onewire":
            msg = "Input type : onewire"
            print(msg)
            self.log.info(msg)

            ### Define listener for onewire input
            Listener(self.action_onewire, 
                     self.myxpl, 
                     {'schema': 'sensor.basic',
                      'xpltype': 'xpl-trig',
                      'type': 'temp',
                      'device' : input})

        ### Define listener for activations
        Listener(self.set_state, 
                 self.myxpl, 
                 {'schema': 'bts.basic',
                  'xpltype': 'xpl-cmnd'})

    def set_state(self, message):
        """ set scenario on or off
            @param message : xpl message
        """
        if activated_scenario == "bts_gen":
            self.state = "on"
        else:
            self.state = "off"
        msg = "Scenario is %s" % self.state
        self.log.debug(msg)
        print(msg)

    def explode(self, input):
        """ Explode an input address
            input is "foo:bar" format. foo = type, bar = address
            example : ipx800:ipx-btn3
            @param input : input address
            @return : type, address
        """
        return input.split(":")[0], input.split(":")[1]
       
    def action_ipx800(self, message):
        """ check input and call appropriate action
            @param message : xpl message
        """
        if self.state == "off":
            print("Input change but scenario is off : nothing will be done")
            return
        print("Input change")
        # Get input status
        input_level = message.data['current']

        # If input is HIGH
        if input_level == "HIGH":
            self.make_action("HIGH")
        else:
            self.make_action("LOW")

    def action_onewire(self, message):
        """ check input and call appropriate action
            @param message : xpl message
        """
        if self.state == "off":
            print("Input change but scenario is off : nothing will be done")
            return
        print("Input change")
        # Get input status
        input_temp = message.data['current']

        # If input is HIGH
        if input_temp >= self.threshold:
            self.make_action("HIGH")
        else:
            self.make_action("LOW")

    def make_action(self, action):
        """ make action
            @param action : HIGH, LOW
        """
        if action == "HIGH":
            log = "Make action for HIGH or >="
        else:
            log = "Make action for LOW or <"
        self.log.debug(log)
        print(log)
        for output in self.outputs:
            if action == "HIGH":
                level = "HIGH"
            else:
                # If input is LOW, we send opposite values
                level = self.outputs[output]["level"]
                if level.upper() == "HIGH":
                    level = "LOW"
                else:
                    level = "HIGH"
            if self.outputs[output]["type"] == "ipx800":
                self.set_ipx800_relay(self.outputs[output]["address"], level)
            if self.outputs[output]["type"] == "x10":
                self.set_x10_relay(self.outputs[output]["address"], level)

    def set_ipx800_relay(self, address, level):
        """ set an ipx800 relay level at HIGH/LOW
            @param addres : ipx800 relay address
            @param level : HIGH/LOW
        """
        log = "ipx800 : Set '%s' to '%s'" % (address, level)
        self.log.debug(log)
        print log
        msg = XplMessage()
        msg.set_type("xpl-cmnd")
        msg.set_schema('control.basic')
        msg.add_data({'device' :  address})
        msg.add_data({'type' :  'output'})
        msg.add_data({'current' :  level})
        self.myxpl.send(msg)

    def set_x10_relay(self, address, level):
        """ set a x10 module at on (HIGH)/off(LOW)
            @param addres : x10 address
            @param level : HIGH/LOW
        """
        log = "x10 : Set '%s' to '%s'" % (address, level)
        self.log.debug(log)
        print log
        msg = XplMessage()
        msg.set_type("xpl-cmnd")
        msg.set_schema('x10.basic')
        msg.add_data({'device' :  address})
        if level == "HIGH":
            cmd = "on"
        else:
            cmd = "off"
        msg.add_data({'command' :  cmd})
        self.myxpl.send(msg)



if __name__ == "__main__":
    BtsGeneral()
