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
import json

from mq_reqrep_utils import MqRep
from domogik.xpl.lib.scenario.manager import ScenarioManager
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.mq.reqrep.mq_reqrep_utils import REQ_PREFIX


class ScenarioFrontend(XplPlugin):
    """ This class provides an interface to MQ system to allow Scenarii management.
    """

    def __init__(self):
        XplPlugin.__init__(self, name='scenario')
        self.add_stop_cb(self.shutdown)
        self.log.info("Scenario manager initialized")
        self._mq = MqRep()
        self._backend = ScenarioManager(self.log)
        self.add_stop_cb(self.shutdown)
        self.log.info("Scenario Frontend and Manager initialized, let's wait for some work.")
        self.waitmessages()

    def waitmessages(self):
        """ This method actually wait for some message
        """
        while not self.should_stop():
            j, o = self._mq.wait_for_request()  # This blocks unitl request is received
            if self.__validate(o):
                self.log.debug("Process message %s" % j)
                rep = self.process_message(o)  # Let's process the message
                self._mq.send_reply(rep)
            else:
                self.log.info('Got useless message %s' % j)

    def __validate(self, o):
        """ Ensure a request is of some interest for us.
        """
        return ((o.type == REQ_PREFIX) and
                (o.category in ['scenario_condition', 'scenario_test', 'scenario_parameter', 'scenario_action']))

    def process_message(self, msg):
        """ Do real work with message
        The message `msg` is supposed to be valid, so we don't care about type/category
        @param msg : object representation of message
        The expected format of msg.content is a hash where each key/val pair is a parameter
        of the inner function
        @return a string ready to be sent as content to `send_reply`
        The content will always be of the form  : {'status': 'ok|error', 'details': 'some error message|empty', 'content': some_other_struct}
        """
        mapping = {'test':
                   {
                   'list': self._backend.list_tests,
                   'new': self._backend.ask_instance,
                   },
                   'condition':
                   {
                   'list': self._backend.list_conditions,
                   'new': self._backend.create_condition,
                   },
                   'parameter':
                   {
                   'list': self._backend.list_parameters,
                   }
        }
        try:
            return mapping[msg.category.split('_')[1]][msg.action](msg.content)
        except:
            self.log.error("Exception occured during message processing.")
            trace = str(traceback.format_exc())
            self.log.debug(trace)
            return json.dumps({'status': 'error', 'details': trace})

    def shutdown(self):
        """ Shutdown Scenario
        """
        self._backend.shutdown()
