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

    def __init__(self, log=None):
        AbstractAction.__init__(self, log)
        self.log = log
        self.set_description("Start a certain command")
        # let's get the devices list
        self.cmds_list = []
        try:
            cli = MQSyncReq(zmq.Context())
            msg = MQMessage()
            msg.set_action('device.get')
            json_devices = cli.request('dbmgr', msg.get(), timeout=10).get()[1]
            devices = json.loads(json_devices)['devices']
            for dev in devices:
                name = dev['name']
                for cmd_idx in dev['commands']:
                    cmd_name = dev['commands'][cmd_idx]['name']
                    cmd_id = dev['commands'][cmd_idx]['id']
                    self.cmds_list.append(['{0} : {1}'.format(name, cmd_name), 
                                         '{0}'.format(cmd_id)])
        except:
            #self.log.error("Error while getting devices list : {0}".format(traceback.format_exc()))
            print("Error while getting devices list : {0}".format(traceback.format_exc()))
            pass


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
                self.log.error("Command sending to XPL gw failed: {0}".format(res))
        else:
            self.log.error("XPL gw did not respond")


    def get_expected_entries(self):
        #the_commands = [['a', 'A'], ['b', 'B']]
        the_commands = self.cmds_list
        return {
                 'cmdid': {'type': 'list',
                          'description': 'The command to start',
                          'values': the_commands,
                          'default': 0},
                 'cmdparams': {'type': 'dict',
                          'description': 'The parameters for this command (ui needs to look them up in the DB)',
                          'default': {}}
               }
