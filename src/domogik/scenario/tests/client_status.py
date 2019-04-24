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

@author: Nico84dev
@copyright: (C) 2007-2019 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.tests.abstract import AbstractTest
from domogik.common.database import DbHelper
from domogik.common.utils import parse_client_id
from time import sleep, time
import zmq

class AbstractStatusTest(AbstractTest):
    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self._subMessages.append( 'plugin.status' )
        self._clientId = params
        self.set_description(u"Check if status/date changes for a client with id {0}".format(self._clientId))
        self.log = log
        self._db = DbHelper(owner="Abstract Client Status")
        self._res = None
        if self._clientId is not None :
            self._client_ref = parse_client_id(self._clientId)
            # get initital info from db
            with self._db.session_scope():
                status = self._db.list_plugin_history(self._client_ref['type'], self._client_ref['name'], self._client_ref['host'])
                if status != []:
                    self._res = status[0]['status']

    def destroy(self):
        """ Destroy fetch thread
        """
        AbstractTest.destroy(self)

    def on_message(self, did, msg):
        """Receive message from MQ sub"""
        if self._client_ref:
#    {u'comment': u'', u'host': u'vmdevubuntu16', u'type': u'plugin', u'name': u'ozwave',  u'event': u'alive'}
            if 'name' in msg and msg['name'] == self._client_ref['name']:
                if 'type' in msg and 'host' in msg:
                    if msg['type'] == self._client_ref['type'] and msg['host'] == self._client_ref['host'] :
                        self.log.debug(u"{0} : received MQ message : {1}. Please notice that if a scenario which use several of this sensor block is currently being evaluated, only one value is processed (in case the sensor values change too fast!)".format(self.__class__.__name__, msg))
                        self.handle_message(did, msg)



class StatusTest(AbstractStatusTest):
    """ Status test : evaluate a client status
    # params == the clientId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractStatusTest.__init__(self, log, trigger, cond, params)
        self.add_parameter(u"usage", "sensor_usage.SensorUsageParameter")
        self._time = time()
        self._res_old = None
        self._time_old = None
        self._dummies = []

    def handle_message(self, did, msg):
        self._time = time()
        self._res = msg['event']
        self.log.debug(u"{0} : Set status value = '{1}' for client id '{2}'. Trigger raised! Please notice that if a scenario which use several of this sensor block is currently being evaluated, only one trigger is processed to avoid running several times the same test.".format(self.__class__.__name__, self._res, self._clientId))
        for dummy in self._dummies :
            dummy.handle_message(did, msg, self._time)
        self._trigger(self)

    def evaluate(self):
        """ Evaluate the sensor value
        """
        p = self.get_raw_parameters()
        u = p["usage"]
        usage = u.evaluate()

        if usage == "value":
            self.log.debug(u"Evaluate {0} '{1}' in mode '{2}' to '{3}'. Type is '{4}'".format(self.__class__.__name__,self._clientId, usage, self._res, type(self._res)))
            self._res_old = self._res
            self._time_old = self._time
            return self._res
        elif usage == "trigger_on_change":
            if self._res_old != None and self._res != self._res_old:   # not sensor startup or sensor value changed
                has_changed = True
            else:
                has_changed = False
            self.log.debug(u"Evaluate {0} '{1}' in mode '{2}' to '{3}'. Type is '{4}'".format(self.__class__.__name__,self._clientId, usage, has_changed, type(has_changed)))
            self._res_old = self._res
            self._time_old = self._time
            return has_changed
        elif usage == "trigger_on_all":
            #print("R vs Ro : {0} vs {1}".format(self._res, self._res_old))
            #print("T vs To : {0} vs {1}".format(self._time, self._time_old))
            if self._res_old != None and ((self._res != self._res_old) or (self._time != self._time_old)):   # not sensor startup or sensor value changed or date changed
                self.log.debug(u"Evaluate {0} '{1}' in mode '{2}' to '{3}'. Type is '{4}'".format(self.__class__.__name__, self._clientId, usage, True, type(True)))
                self._res_old = self._res
                self._time_old = self._time
                return True
            else:    # init of the sensor block
                self._res_old = self._res
                self._time_old = self._time
                return False
        else:
            self.log.error(u"Bad usage used for statusTest! Usage choosed ='{0}'".format(usage))
            return None

    def register_dummy(self, dummy):
        """ Register a dummy test to push updted value """
        if dummy not in self._dummies :
            self._dummies.append(dummy)

class StatusTestDummy(StatusTest):
    """ Status test : evaluate a sensor by cloning (dummy) a main StatusTest
    # params == the clientId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        StatusTest.__init__(self, log, trigger, cond, params)
        self._subMessages = [] # disable  'device-stats'   MQ Message

    def on_message(self, did, msg):
        pass

    def handle_message(self, did, msg, time=0):
        self._time = time
        self._res = msg['event']
        self.log.debug(u"{0} : Set status value = '{1}' for client id '{2}'.".format(self.__class__.__name__, self._res, self._clientId))

class StatusValue(StatusTest):
    """ Status Value : evaluate a sensor without triggering scenario evaluation
    # params == the clientId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        StatusTest.__init__(self, log, trigger, cond, params)

    def handle_message(self, did, msg):
        self._time = time()
        self._res = msg['event']
        self.log.debug(u"{0} : Set status value = '{1}' for client id '{2}'. No trigger evaluation need.".format(self.__class__.__name__, self._res, self._clientId))
        for dummy in self._dummies :
            dummy.handle_message(did, msg, self._time)

class StatusValueDummy(StatusValue):
    """ Status Value : evaluate a sensor by cloning (dummy) a main SensorValue
    # params == the clientId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        StatusValue.__init__(self, log, trigger, cond, params)
        self._subMessages = [] # disable  'plugin.status'   MQ Message

    def on_message(self, did, msg):
        pass

    def handle_message(self, did, msg, time=0):
        self._time = time
        self._res = msg['event']
        self.log.debug(u"{0} : Set status value = '{1}' for client id '{2}'.".format(self.__class__.__name__, self._res, self._clientId))
