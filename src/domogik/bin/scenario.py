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

This plugin manages scenarii, it provides MQ interface

Implements
==========


@author: Maxence Dunnewind
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik.scenario.manager import ScenarioManager
from domogik.xpl.common.plugin import Plugin
#from domogikmq.reqrep.worker import MQRep
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
import zmq
import time

class ScenarioFrontend(Plugin):
    """ This class provides an interface to MQ system to allow Scenarii management.
    """

    def __init__(self):
        Plugin.__init__(self, name = 'scenario', log_prefix='core_')
        ### check that needed services are up on MQ side
        cli = MQSyncReq(zmq.Context())
        mq_services = None
        while mq_services == None or 'xplgw' not in mq_services:
            mq_services_raw = cli.rawrequest('mmi.services', '', timeout=10)
            if mq_services_raw != None:
                mq_services = str(mq_services_raw[0]).replace(" ", "").split(",")
            self.log.info("Checking for MQ service 'xplgw'. Current list is : {0}".format(mq_services))
            if mq_services == None or 'xplgw' not in mq_services:
                self.log.debug("Needed MQ services 'xplgw' not yet available : waiting")
                time.sleep(3)
        self.log.info("Needed MQ services available : continuing startup")

        ### start the scenario stuff
        self._backend = ScenarioManager(self.log)
        self.add_stop_cb(self.end)
        self.add_stop_cb(self.shutdown)
        self.log.info(u"Scenario Frontend and Manager initialized, let's wait for some work.")
        self.ready()

    def on_mdp_request(self, msg):
        """ Do real work with message
        msg.get_action() shoult contain XXXX.YYYYYY
        with XXXX in [test, condition, parameter]
        YYYYY in [list, new, etc ...]
        """
        mapping = {'test':
                    {
                        'list': self._backend.list_tests,
                    },
                    'scenario':
                    {
                        'list': self._backend.list_conditions,
                        'new': self._backend.create_scenario,
                        'update': self._backend.update_scenario,
                        'delete': self._backend.del_scenario,
                        'get': self._backend.get_parsed_condition,
                        'evaluate': self._backend.eval_condition,
                        'enable': self._backend.enable_scenario,
                        'disable': self._backend.disable_scenario,
                        'test': self._backend.test_scenario
                    },
                    'action':
                    {
                        'list': self._backend.list_actions,
                    }
                }
        try:
            if msg.get_action().split('.')[0] not in mapping.keys():
                self._mdp_reply(msg.get_action(), {"status" : "error", "details": "{0} not in {1}".format(msg.get_action().split('.')[0], mapping.keys())})
            else:
                if msg.get_action().split('.')[1] not in mapping[msg.get_action().split('.')[0]].keys():
                    self._mdp_reply(msg.get_action(), {"status" : "error", "details": "{0} not in {1}".format(msg.get_action().split('.')[1], mapping[msg.get_action().split('.')[0]].keys())})
                else:
                    if msg.get_data() == {}:
                        payload = mapping[msg.get_action().split('.')[0]][msg.get_action().split('.')[1]]()
                    else:
                        print(msg.get_data())
                        payload = mapping[msg.get_action().split('.')[0]][msg.get_action().split('.')[1]](**msg.get_data())
                    self._mdp_reply(msg.get_action(), payload)
        except:
            self.log.error(u"Exception occured during message processing.")
            trace = str(traceback.format_exc())
            self.log.debug(trace)
            self._mdp_reply(msg.get_action(), {"status": "errpr", "details": trace})

    def _mdp_reply(self, action, payload):
        msg = MQMessage()
        msg.set_action(action)
        msg.add_data('result', payload)
        self.reply(msg.get())

    def end(self):
        """ Shutdown Scenario
        """
        self._backend.shutdown()


if __name__ == "__main__":
    ScenarioFrontend()
