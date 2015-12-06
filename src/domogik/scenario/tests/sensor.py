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
from domogik.common.database import DbHelper
from time import sleep
from threading import Thread, Event

class SensorTest(AbstractTest):
    """ Sensor test
    # params == the sensorId to check the value for
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self._sensorId = params
        self.set_description("Check The value for a sensor with id {0}".format(self._sensorId))
        self.log = log
        self._db = DbHelper()
        self._res = None
        self._dataType = None
        self._dt_parent = None
        # get info from db
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
        # set new val
        self._res = self._convert(self._res)
        # start the thread
        self._event = Event()
        self._fetch_thread = Thread(target=self._fetch,name="pollthread")
        self._fetch_thread.start()

    def _fetch(self):
        while not self._event.is_set():
            new = None
            with self._db.session_scope():
                sensor = self._db.get_sensor(self._sensorId)
                if sensor is not None:
                    new = self._convert(sensor.last_value)
            if self._res != new:
                self._res = new
                self._trigger(self)
            sleep(2)

    def _convert(self, val):
        if self._dt_parent == "DT_Number":
            if val != None:
                return float(val)
            else:
                return None
        else:
            return val

    def evaluate(self):
        """ Evaluate if the text appears in the content of the page referenced by url
        """
        self.log.debug("SensorTest {0}: evaluate to {1}".format(self._sensorId, self._res)) 
        return self._res

    def destroy(self):
        """ Destroy fetch thread
        """
        self._event.set()
        self._fetch_thread.join()
        AbstractTest.destroy(self)

if __name__ == "__main__":
    import logging

    def mytrigger(test):
        print "Trigger called by test %s, refreshing state" % test
        st = TEST.evaluate()
        print "state is %s" % st

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
    data = { "sensor": { "sensor_id" : 1072 },
             "value":  { "text" : "on" }
    }
    logger.debug("Set parameters values")
    st.fill_parameters(data)
    logger.debug("I sleep 5s")

    st.evaluate()

    ######### TODO : finish the below part 
    print "updating with good text"
    data = { "url": { "urlpath" : "http://people.dunnewind.net/maxence/domogik/test.txt",
                    "interval": "5"
    },
    "text": {
        "text" : "randomtext"
    }
    }
    print "===="
    TEST.fill_parameters(data)
    print "===="
    print "I sleep 5s"
    sleep(5)
    print "Trying to evaluate : %s" % TEST.evaluate()
    TEST.destroy()
