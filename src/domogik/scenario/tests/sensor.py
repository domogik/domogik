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

@author: Cereal
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.tests.abstract import AbstractTest
from domogik.common.database import DbHelper
from time import sleep, time
import zmq

class AbstractSensorTest(AbstractTest):
    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self._subMessages.append( 'device-stats' )
        self._sensorId = params
        self.set_description(u"Check if value/date changes for a sensor with id {0}".format(self._sensorId))
        self.log = log
        self._db = DbHelper(owner="Abstract Sensor")
        self._res = None
        self._dataType = None
        self._dt_parent = None
        # get initital info from db
        with self._db.session_scope():
            sensor = self._db.get_sensor(self._sensorId)
            if sensor is not None:
                self._res = sensor.last_value
                self._dataType = sensor.data_type
        # find the parent dt type
        if cond:
            dt_parent = self._dataType
            while 'parent' in cond.datatypes[dt_parent] and cond.datatypes[dt_parent]['parent'] != None:
                dt_parent = cond.datatypes[dt_parent]['parent']
            self._dt_parent = dt_parent

    def destroy(self):
        """ Destroy fetch thread
        """
        AbstractTest.destroy(self)

    def on_message(self, did, msg):
        """Receive message from MQ sub"""
        if self._sensorId:
            if 'sensor_id' in msg:
                if int(msg['sensor_id']) == int(self._sensorId):
                    self.log.debug(u"{0} : received MQ message : {1}. Please notice that if a scenario which use several of this sensor block is currently being evaluated, only one value is processed (in case the sensor values change too fast!)".format(self.__class__.__name__, msg))
                    self.handle_message(did, msg)



class SensorTest(AbstractSensorTest):
    """ Sensor test : evaluate a sensor
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractSensorTest.__init__(self, log, trigger, cond, params)
        self.add_parameter(u"usage", "sensor_usage.SensorUsageParameter")
        self._res = self._convert(self._res)
        self._time = time()
        self._res_old = None
        self._time_old = None
        self._dummies = []

    def handle_message(self, did, msg):
        self._time = time()
        self._res = self._convert(msg['stored_value'])
        self.log.debug(u"{0} : Set sensor value = '{1}' for sensor id '{2}'. Trigger raised! Please notice that if a scenario which use several of this sensor block is currently being evaluated, only one trigger is processed to avoid running several times the same test.".format(self.__class__.__name__, self._res, self._sensorId))
        for dummy in self._dummies :
            dummy.handle_message(did, msg, self._time)
        self._trigger(self)

    def _convert(self, val):
        if self._dt_parent == "DT_Number":
            if val != None:
                return float(val)
            else:
                return 0
        elif self._dt_parent == "DT_Bool":
            if val == "1":
                return True
            else:
                return False
        elif self._dataType == "DT_Time":
            if val != None:
                tmp = val.split(":")
                if len(tmp) < 2:   # bad value
                    return 0
                else:
                    try:
                        new =  int(tmp[0]) * 60 + int(tmp[1])
                        #self.log.debug("DT_Time : convert '{0}' to '{1}'".format(val, new))
                        return new
                    except:
                        self.log.debug(u"Error while converting DT_Time value in mminutes. Value='{0}'".format(val))
                        return 0
            else:
                return 0
        else:
            return val

    def evaluate(self):
        """ Evaluate the sensor value
        """
        p = self.get_raw_parameters()
        u = p["usage"]
        usage = u.evaluate()

        if usage == "value":
            self.log.debug(u"Evaluate {0} '{1}' in mode '{2}' to '{3}'. Type is '{4}'".format(self.__class__.__name__,self._sensorId, usage, self._res, type(self._res)))
            self._res_old = self._res
            self._time_old = self._time
            return self._res
        elif usage == "trigger_on_change":
            if self._res_old != None and self._res != self._res_old:   # not sensor startup or sensor value changed
                has_changed = True
            else:
                has_changed = False
            self.log.debug(u"Evaluate {0} '{1}' in mode '{2}' to '{3}'. Type is '{4}'".format(self.__class__.__name__,self._sensorId, usage, has_changed, type(has_changed)))
            self._res_old = self._res
            self._time_old = self._time
            return has_changed
        elif usage == "trigger_on_all":
            #print("R vs Ro : {0} vs {1}".format(self._res, self._res_old))
            #print("T vs To : {0} vs {1}".format(self._time, self._time_old))
            if self._res_old != None and ((self._res != self._res_old) or (self._time != self._time_old)):   # not sensor startup or sensor value changed or date changed
                self.log.debug(u"Evaluate {0} '{1}' in mode '{2}' to '{3}'. Type is '{4}'".format(self.__class__.__name__, self._sensorId, usage, True, type(True)))
                self._res_old = self._res
                self._time_old = self._time
                return True
            else:    # init of the sensor block
                self._res_old = self._res
                self._time_old = self._time
                return False
        else:
            self.log.error(u"Bad usage used for sensorTest! Usage choosed ='{0}'".format(usage))
            return None

    def register_dummy(self, dummy):
        """ Register a dummy test to push updted value """
        if dummy not in self._dummies :
            self._dummies.append(dummy)

class SensorTestDummy(SensorTest):
    """ Sensor test : evaluate a sensor by cloning (dummy) a main SensorTest
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        SensorTest.__init__(self, log, trigger, cond, params)
        self._subMessages = [] # disable  'device-stats'   MQ Message

    def on_message(self, did, msg):
        pass

    def handle_message(self, did, msg, time=0):
        self._time = time
        self._res = self._convert(msg['stored_value'])
        self.log.debug(u"{0} : Set sensor value = '{1}' for sensor id '{2}'.".format(self.__class__.__name__, self._res, self._sensorId))

class SensorValue(SensorTest):
    """ Sensor Value : evaluate a sensor without triggering scenario evaluation
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        SensorTest.__init__(self, log, trigger, cond, params)

    def handle_message(self, did, msg):
        self._time = time()
        self._res = self._convert(msg['stored_value'])
        self.log.debug(u"{0} : Set sensor value = '{1}' for sensor id '{2}'. No trigger evaluation need.".format(self.__class__.__name__, self._res, self._sensorId))
        for dummy in self._dummies :
            dummy.handle_message(did, msg, self._time)

class SensorValueDummy(SensorValue):
    """ Sensor Value : evaluate a sensor by cloning (dummy) a main SensorValue
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        SensorValue.__init__(self, log, trigger, cond, params)
        self._subMessages = [] # disable  'device-stats'   MQ Message

    def on_message(self, did, msg):
        pass

    def handle_message(self, did, msg, time=0):
        self._time = time
        self._res = self._convert(msg['stored_value'])
        self.log.debug(u"{0} : Set sensor value = '{1}' for sensor id '{2}'.".format(self.__class__.__name__, self._res, self._sensorId))
