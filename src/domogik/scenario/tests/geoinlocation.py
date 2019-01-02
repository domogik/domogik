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
from shapely.geometry import Polygon, Point
from shapely.ops import transform
from functools import partial
import pyproj

from time import time, sleep
import json

class GeoInLocTest(AbstractTest):
    """ GeoInLocTest : evaluate a location to another.
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
#        print(u'GeoInLocTest init param :',  params)
        self._testId = params
        self.set_description("Test geo location relative to another")
        self.add_parameter("person_hyst", "text.TextParameter")
        self.add_parameter("operator", "location_operator.LocationOperatorParameter")
        self.add_parameter("loc_hyst", "text.TextParameter")
        self._personState = {'status': '', 'time': time()}
        self._dummies = []
        self._parent = None

    def _processState(self, newState):
        if self._personState['status'] != newState :
            if newState == 'present' :
                if self._personState['status'] in ['absent', 'leave'] :
                   newState = 'enter'
                elif self._personState['status'] == 'enter' :
                    newState = 'present'
            elif newState == 'absent' :
                if self._personState['status'] in ['present', 'enter'] :
                   newState = 'leave'
                elif self._personState['status'] == 'leave' :
                    newState = 'absent'
        if self._personState['status'] == '' : self._propagate_state({'status': newState, 'time': time()})
        self._personState = {'status': newState, 'time': time()}
        return newState

    def getHystersis(self, buffer):
        newBuffer = float(buffer)
        if self._personState['status'] in ['absent', 'leave'] :
            newBuffer = 0
#        print(u'    getHysterisis : {0} (buffer : {1}=>{2})'.format(self._personState, buffer, newBuffer))
        return newBuffer

    def getPolyBuffered(self, poly, bufferValue):
        bufferValue = float(bufferValue)
        if bufferValue != 0 :
            # Transform to metric
            p1Buffer = transform(
                partial(
                    pyproj.transform,
                    pyproj.Proj(init='EPSG:4326'),  # EPSG:4326 est WGS 84
                    pyproj.Proj(
                        proj='aea',
                        lat1=poly.bounds[1],
                        lat2=poly.bounds[3]
                    )
                ),
                poly)
            p2Buffer = p1Buffer.buffer(bufferValue)
#            print("********************* area (m2) : ", p2Buffer.area)
            # transforn to geo coordinate
            result = transform(
                partial(
                    pyproj.transform,
                    pyproj.Proj(
                        proj='aea',
                        lat1=p2Buffer.bounds[1],
                        lat2=p2Buffer.bounds[3]
                    ),
                    pyproj.Proj(init='EPSG:4326')  # EPSG:4326 est WGS 84
                ),
                p2Buffer)
            return result
        else : return poly

    def evaluate(self, gpsPoint=None, location=None):
        """ Evaluate the person position compare to location
        """
        self._personState['time'] = time()
        params = self.get_raw_parameters()
#        print("**** eval : ", params)
        person_hyst = params["person_hyst"].evaluate()
        operator = params["operator"].evaluate()
        loc_hyst = params["loc_hyst"].evaluate()
#        print(type(gpsPoint), type(location), operator, person_hyst, loc_hyst)
        if gpsPoint is None:
            return None
        elif  location is None:
            return None
        else:
            if type(gpsPoint) in [str, unicode] :
                try :
                    point = gpsPoint.split(",")
                    gpsPoint = {'lat': float(point[0]), 'lng':float(point[1])}
                except:
                    self.log.warning(u"Error while converting DT_CoordD value 1 in GPS. Value='{0}'".format(gpsPoint))
                    return None
            loc_buffer =self.getHystersis(loc_hyst)
            # Create shapely objects
            p = Point(gpsPoint['lat'], gpsPoint['lng'])
            p1 = self.getPolyBuffered(p, person_hyst)
            if location['type'] == 'circle' :
                p = Point(location['lat'], location['lng'])
                p2 = self.getPolyBuffered(p, float(location['area']) + loc_buffer)
                state = self._processState('present' if p1.intersects(p2) else 'absent')
                result = operator == state
            elif location['type'] == 'polygon' :
                state = None
                result = False
                for poly in json.loads(location['area']) :
                    p = Polygon(poly)
                    p2 = self.getPolyBuffered(p, loc_buffer)
                    state = self._processState('present' if p1.intersects(p2) else 'absent')
                    if operator == state :
                        result = True
                        break
            else :
                self.log.warning(u"Error area type unknown. Value='{0}'".format(location))
                return None
            self.log.debug("Evaluate {0} : {1} {2} {3} = {4}".format(self.__class__.__name__, gpsPoint, operator, location, result))
            if result: self._propagate_state(self._personState)
            return result

    def register_dummy(self, dummy):
        """ Register a dummy test to push updated value """
        if dummy not in self._dummies :
            self._dummies.append(dummy)
            dummy.register_parent(self)

    def _propagate_state(self, personState):
        if self._parent is None :
            self._personState = personState
            for dummy in self._dummies :
                dummy.setPersonState(personState)
        else :
            self._parent._propagate_state(personState)

    def get_blockly(self):
        return """this.appendValueInput("person")
                        .setCheck("sensor.SensorTest")
                        .appendField("Buffer")
                        .appendField(new Blockly.FieldNumber(0), "person_hyst")
                        .appendField("(m)");
                  this.appendDummyInput()
                        .appendField(new Blockly.FieldDropdown([["present in","present"], ["absent from","absent"], ["enter in","enter"], ["leave","leave"]]), "op");
                  this.appendValueInput("location")
                        .setCheck("location.LocationTest");
                  this.appendDummyInput()
                        .appendField("Buffer")
                        .appendField(new Blockly.FieldNumber(0), "loc_hyst")
                        .appendField("(m)");
                  this.setInputsInline(true);
                  this.setOutput(true, null);
                  this.setColour(230);
                  this.setTooltip("Test person position relative to a fixed location. Parameters : Buffer person (in meter) used for uncertain positioning. Buffer location (in meter) used for detect area leave and avoid unnecessary triggering of switching between entry and leave from area limits.");
                  this.setHelpUrl("");"""

class GeoInLocTestDummy(GeoInLocTest):
    """ GeoInLocTestDummy : evaluate a location to another by cloning (dummy) a main GeoInLocTest
    """
    def __init__(self, log = None, trigger = None, cond = None, params = None):
        GeoInLocTest.__init__(self, log, trigger, cond, params)
        self._evalResult = None
        self._parent = None

    def register_parent(self, parent):
        self._parent = parent

    def setPersonState(self, state):
        """ Evaluate allready evaluate with true result
            Memorized new state
        """
        self.log.debug("Set state from propogate {0} : {1}".format(self.__class__.__name__, state))
        self._personState = state

if __name__ == "__main__":
    import logging
    TEST = None

    def mytrigger(test):
        print("Trigger called by test {0}, refreshing state".format(test))
        st = TEST.evaluate()
        print("state is {0}".format(st))

    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)
    TEST = GeoInLocTest(logging, trigger = mytrigger)
    print(TEST)
    print("getting parameters")
    p = TEST.get_parameters()
    print(p)
    print("====")
    print("Trying to evaluate : {0}".format(TEST.evaluate()))
    print("====")
    print("set data for parameters geo in location")
    data = { "person.person_id" : "3" , "operator.operator": "present", "location.location_id" : "1" }
    TEST.fill_parameters(data)
    sleep(5)
    print("Trying to evaluate : {0}".format(TEST.evaluate()))
    TEST.destroy()
