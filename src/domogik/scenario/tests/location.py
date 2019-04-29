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

@author: Nico0084 <nico84dev@gmail.com>
@copyright: (C) 2007-2018 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.tests.abstract import AbstractTest
from domogik.common.database import DbHelper
from time import sleep, time
import zmq

class AbstractLocationTest(AbstractTest):
    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self._subMessages.append( 'location.update' )
        self._locationId = params
        self.set_description(u"Get informations of location id {0}".format(self._locationId))
        self.log = log
        self._db = DbHelper(owner="Abstract location")
        self._res = None
        # get initital info from db
        with self._db.session_scope():
            params = self._db.get_location_all_param(self._locationId)
            if params is not None:
                self._res = {}
                for p in params :
                    self._res[p.key] = p.value

    def destroy(self):
        """ Destroy fetch thread
        """
        AbstractTest.destroy(self)

    def on_message(self, did, msg):
        """Receive message from MQ sub"""
        if self._locationId:
            if 'location_id' in msg:
                if int(msg['location_id']) == int(self._locationId):
                    self.log.debug(u"{0} : received MQ message : {1}. Please notice that if a scenario which use several of this location block is currently being evaluated, only one value is processed (in case the sensor values change too fast!)".format(self.__class__.__name__, msg))
                    self.handle_message(did, msg)

class LocationTest(AbstractLocationTest):
    """ location test : evaluate a sensor
    # params == the locationId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractLocationTest.__init__(self, log, trigger, cond, params)
        self._time = time()
        self._res_old = None
        self._time_old = None
        self._dummies = []

    def handle_message(self, did, msg):
        self._time = time()
        self._res = msg['params']
        self.log.debug(u"{0} : Set location value = '{1}' for location id '{2}'. Trigger raised! Please notice that if a scenario which use several of this sensor block is currently being evaluated, only one trigger is processed to avoid running several times the same test.".format(self.__class__.__name__, self._res, self._locationId))
        for dummy in self._dummies :
            dummy.handle_message(did, msg, self._time)
        self._trigger(self)

    def evaluate(self):
        """ Evaluate the location value
        """
        self._res_old = self._res
        self._time_old = self._time
        res = self._res
        if self._res is not None :
            if 'ctrl_type' in self._res :
                ctrlType = self._res['ctrl_type']
                area = self._res['ctrl_area']
            else :
                ctrlType = 'circle'
                area = self._res['radius']
            res = {'lat' : float(self._res['lat']), 'lng' : float(self._res['lng']), 'type': ctrlType, 'area': area}
        self.log.debug(u"Evaluate {0} '{1}' to '{2}'. Type is '{3}'".format(self.__class__.__name__,self._locationId, res, type(res)))
        for dummy in self._dummies :
            dummy.setEvalResult(res)
        return res

    def register_dummy(self, dummy):
        """ Register a dummy test to push updted value """
        if dummy not in self._dummies :
            self._dummies.append(dummy)

class LocationTestDummy(LocationTest):
    """ Location test : evaluate a location by cloning (dummy) a main LocationTest
    # params == the locationId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        LocationTest.__init__(self, log, trigger, cond, params)
        self._subMessages = [] # disable  'location.update'   MQ Message
        self._evalRes = None

    def on_message(self, did, msg):
        pass

    def handle_message(self, did, msg, time=0):
        self._time = time
        self._res = msg['params']
        self.log.debug(u"{0} : Set location value = '{1}' for location id '{2}'.".format(self.__class__.__name__, self._res, self._locationId))

    def setEvalResult(self, res):
        self._evalRes = res

    def evaluate(self):
        self.log.debug(u"Evaluate {0} '{1}' to '{2}'. Type is '{3}'".format(self.__class__.__name__,self._locationId, self._evalRes, type(self._evalRes)))
        return self._evalRes

class LocationValue(LocationTest):
    """ Sensor Value : evaluate a sensor without triggering scenario evaluation
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        LocationTest.__init__(self, log, trigger, cond, params)

    def handle_message(self, did, msg):
        self._time = time()
        self._res = msg['params']
        self.log.debug(u"{0} : Set location value = '{1}' for location id '{2}'. No trigger evaluation need.".format(self.__class__.__name__, self._res, self._locationId))
        for dummy in self._dummies :
            dummy.handle_message(did, msg, self._time)

class LocationValueDummy(LocationValue):
    """ Sensor Value : evaluate a sensor by cloning (dummy) a main SensorValue
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        LocationValue.__init__(self, log, trigger, cond, params)
        self._subMessages = [] # disable  'location.update'   MQ Message

    def on_message(self, did, msg):
        pass

    def handle_message(self, did, msg, time=0):
        self._time = time
        self._res = msg['params']
        self.log.debug(u"{0} : Set location value = '{1}' for location id '{2}'.".format(self.__class__.__name__, self._res, self._locationId))
