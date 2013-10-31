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

from domogik.common.scenario.actions.abstract import AbstractAction
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
import zmq

class CommandAction(AbstractAction):
    """ Simple action that log something in scenario logfile
    """

    def __init__(self, log=None):
        AbstractAction.__init__(self, log)
        self.set_description("Start a certain command")

    def do_action(self, condition, tests):
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('cmd.send')
        msg.add_data('cmdid', self._params['cmdid'])
        msg.add_data('cmdparams', self._params['cmdparams'])
        # do the request
        res = cli.request('xplgw', msg.get(), timeout=10)
        if res:
            data = res.get_data()
            if not data['status']:
                self._log.error("Command sending to XPL gw failed: {0}".format(res))
        else:
            self._log.error("XPL gw did not respond")


    def get_expected_entries(self):
        return {
                 'cmdid': {'type': 'integer',
                          'description': 'The command to start',
                          'default': 0},
                 'cmdparams': {'type': 'dict',
                          'description': 'The parameters for this command (ui needs to look them up in the DB)',
                          'default': {}}
               }
