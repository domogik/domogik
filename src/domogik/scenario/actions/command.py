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

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.actions.abstract import AbstractAction
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
import zmq
import json
import traceback

class CommandAction(AbstractAction):
    """ Simple action that log something in scenario logfile
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log, params)
        self.log = log
        self.set_description("Start a certain command")
        self._cmdId = params

    def do_action(self):
        print self._params
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('cmd.send')
        msg.add_data('cmdid', self._cmdId)
        msg.add_data('cmdparams', self._params)
        # do the request
        res = cli.request('xplgw', msg.get(), timeout=10)
        if res:
            data = res.get_data()
            if not data['status']:
                self.log.error("Command sending to XPL gw failed: {0}".format(res))
        else:
            self.log.error("XPL gw did not respond")

    def get_expected_entries(self):
        return {
                 'cmdparams': {'type': 'dict',
                          'description': 'The parameters for this command',
                          'default': {}}
               }
