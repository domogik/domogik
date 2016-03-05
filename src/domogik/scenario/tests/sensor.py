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
from domogikmq.pubsub.subscriber import MQAsyncSub
from time import sleep
import zmq

class AbstractSensorTest(AbstractTest, MQAsyncSub):
    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self.sub = MQAsyncSub.__init__(self, zmq.Context(), 'scenario-sensor', ['device-stats'])
        self._sensorId = params
        self.set_description("Check if value/date changes for a sensor with id {0}".format(self._sensorId))
        self.log = log
        self._db = DbHelper()
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
                    self.handle_message(did, msg)


class SensorTest(AbstractSensorTest):
    """ Sensor test : evaluate a sensor value when it changes
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractSensorTest.__init__(self, log, trigger, cond, params)
        self._res = self._convert(self._res)

    def handle_message(self, did, msg):
        self._res = self._convert(msg['stored_value'])
        self._trigger(self)

    def _convert(self, val):
        if self._dt_parent == "DT_Number":
            if val != None:
                return float(val)
            else:
                return None
        elif self._dataType == "DT_Time":
            if val != None:
                tmp = val.split(":")
                if len(tmp) < 2:   # bad value
                    return None
                else:
                    try:
                        new =  int(tmp[0]) * 60 + int(tmp[1])
                        #self.log.debug("DT_Time : convert '{0}' to '{1}'".format(val, new))
                        return new
                    except:
                        self.log.debug("Error while converting DT_Time value in mminutes. Value='{0}'".format(val))
                        return None
            else:
                return None
        else:
            return val

    def evaluate(self):
        """ Evaluate the sensor value
        """
        self.log.debug("Evaluate SensorTest '{0}' to '{1}'. Type is '{2}'".format(self._sensorId, self._res, type(self._res))) 
        return self._res

class SensorChangedTest(AbstractSensorTest):
    """ Sensor test : raise True when the value/date change
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractSensorTest.__init__(self, log, trigger, cond, params)
        self._old_res = self._res

    def handle_message(self, did, msg):
        self._res = msg['stored_value']
        # Trigger only if the value changed
        if self._res != self._old_res:
            self._trigger(self)
        self._old_res = self._res

    def evaluate(self):
        """ Evaluate the sensor value
        """
        self.log.debug("Evaluate SensorChangedTest '{0}' : value changed. Return True.".format(self._sensorId, self._res)) 
        return True


if __name__ == "__main__":
    import logging

    def mytrigger(test):
        print("Trigger called by test {0}, refreshing state".format(test))
        print("state is {0}".format(st))

    ### create logger
    FORMAT = "%(asctime)-15s %(message)s"

    logger = logging.getLogger('simple_example')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(FORMAT)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    logger.info("------------------")


    ### test the class
    st = SensorTest(logger, trigger = mytrigger)
    p = st.get_parameters()

    logger.info("==== Evaluate without parameters values ====")
    st.evaluate()

    logger.info("==== Evaluate with parameters values that does not match ====")
    logger.debug("Set values")
    data = { "sensor": { "sensor_id" : 2 },
             "value":  { "text" : "on" }
    }
    logger.debug("Set parameters values")
    st.fill_parameters(data)
    logger.debug("I sleep 5s")

    st.evaluate()

    ######### TODO : finish the below part 
    print("updating with good text")
    data = { "url": { "urlpath" : "http://people.dunnewind.net/maxence/domogik/test.txt",
                    "interval": "5"
    },
    "text": {
        "text" : "randomtext"
    }
    }
    print("====")
    TEST.fill_parameters(data)
    print("====")
    print("I sleep 5s")
    sleep(5)
    print("Trying to evaluate : {0}".format(TEST.evaluate()))
    TEST.destroy()
