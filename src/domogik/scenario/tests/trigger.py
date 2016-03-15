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

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.tests.abstract import AbstractTest
from time import sleep

class Hysteresis(AbstractTest):
    """ Simple test to check if a word is contained in an url
    """

    def __init__(self, log = None, trigger = None, cond=None, params=None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self.set_description("Trigger mode hysteresis")
        # my block id, will be the inetrnal id for this actions block
        self.add_parameter("id", "trigger.idParameter")
        # keep track of the condition
        self._cond = cond

    def evaluate(self):
        """ Evaluate if the actions should be triggered or not
        """
        p = self.get_raw_parameters()
        # if the current state is not the same
        if p['id'].evaluate() != self._cond.state():
            self._cond.state(p['id'].evaluate())
            return True
        else:
            return False

    def get_blockly(self):
        return """this.appendDummyInput()
                .appendField("Trigger mode hysteresis");
                this.appendStatementInput("Run").setCheck(null);
                this.setPreviousStatement(true);
                this.setNextStatement(true);"""
