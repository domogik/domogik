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
from time import sleep

class SensorTest(AbstractTest):
    """ Sensor test
    """

    def __init__(self, log = None, trigger = None, cond = None):
        AbstractTest.__init__(self, log, trigger, cond)
        self.set_description("Check if the value for a sensor is set to a specific value")
        self.add_parameter("sensor", "sensor_id.SensorIdParameter")
        self.add_parameter("value", "text.TextParameter")
        self.log = log

    def evaluate(self):
        """ Evaluate if the text appears in the content of the page referenced by url
        """
        self.log.debug("SensorTest : evaluate") 
        params = self.get_raw_parameters()
        self.log.debug("SensorTest : evaluate : params = {0}".format(params)) 
        sen = params["sensor"]
        val = params["value"]
        if sen.evaluate() == None or val.evaluate() == None:
            self.log.debug("sen.evaluate() == None or val.evaluate() == None ==> returning None")
            return None
        else:
            # check
            
            self.log.debug("Evaluate : sensor={0}, value={1}".format(sen, val))
            self.log.debug("Evaluate : sensor={0}, value={1}".format(sen.evaluate(), val.evaluate()))
            res = False
            return res


TEST = None
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
