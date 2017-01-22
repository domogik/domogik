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
@copyright: (C) 2007-20015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import uuid
try:
    from exceptions import ValueError
except:
    pass
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from domogik.common.logger import Logger
from domogik.common.utils import remove_accents
from domogikmq.pubsub.subscriber import MQAsyncSub
import zmq
import traceback
import logging
import ast
import datetime
from dateutil import parser
from domogik.common.utils import ucode



def to_unicode(data):
    print(u"to_unicode > type='{0}'".format(type(data)))
    if isinstance(data, unicode):
        return data
    else:
        return unicode(str(data), "utf-8")


class ScenarioInstance(MQAsyncSub):
    """ This class provides base methods for the scenarios
    The scenario json looks like:
    {
        "type": "dom_condition",
        "id": "1",
        "IF": {
            "type": "logic_operation",
            "id": "2",
            "OP": "AND",
            "A": {
                "type": "sensor.TextInPageTest",
                "id": "3",
                "sensor_id": "test utl",
                "text": "test txt"
            },
            "B": {
                "type": "logic_negate",
                "id": "4",
                "BOOL": {
                    "type": "textinpage.TextInPageTest",
                    "id": "5",
                    "urlpath": "url",
                    "text": "txt"
                }
            }
        },
        "DO": {
            "type": "command.CommandAction",
            "id": "6",
            "cmdid": "0"
        },
        "deletable": false
    }
    """
    def __init__(self, log, dbid, name, json, disabled, state, db):
        """ Create the instance
        @param log : A logger instance
        @param dbid : The id of this scenario in the db
        @param json : The json describing the scenario
        """
        self._name = name

        # TODO : fix for Russian names for example
        #self._log = log.getChild(remove_accents(name))
        try:
            self._log = log.getChild(ucode(remove_accents(name)).encode('utf-8'))
        except UnicodeDecodeError:
            self._log = log.getChild("SCENARIO")
            self._log.warning("The scenario name encountered an unicode error while trying to set the log line header with the scenario name. The scenario name will not be put in the log line. It will be replaced by 'SCENARIO'")

        self._json = json
        self._disabled = disabled
        self._state = state
        self._dbid = dbid
        self._db = db
        self._sub = None # If not None, then a asyncSubSCriber
        self._subList = []  # A list that keeps all messages that we need to subScribe to
        self._test_instances = {}  # list of test instances already processes. This is used to avoid triggering N time a scenario if there is N time the same test in it

        self.zmq = zmq.Context()
        # datatypes
        self.datatypes = {}
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('datatype.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is not None:
            res = res.get_data()
            if 'datatypes' in res:
                self.datatypes = res['datatypes']

        self._parsed_condition = None
        self._compiled_condition = None
        self._mapping = { 'test': {}, 'action': {} }
        if not self._disabled:
            self._instanciate()

    def enable(self):
        if self._disabled:
            self._disabled = False
            self._instanciate()
            return True
        else:
            return False

    def disable(self):
        if not self._disabled:
            self._disabled = True
            self._clean_instances()
            return True
        else:
            return False

    def state(self, new=None):
        if new:
            self._state = new
            with self._db.session_scope():
                self._db.update_scenario(self._dbid, state=new)
            return True
        else:
            return self._state

    def destroy(self):
        """ Cleanup the class
        """
        self._clean_instances()

    def _clean_instances(self):
        for (uid, item) in self._mapping['action'].items():
            item.destroy()
            del item
        self._mapping['action'] = {}
        for (uid, item) in self._mapping['test'].items():
            item.destroy()
            del item
        self._mapping['test'] = {}
        self._test_instances = {}
        self._sub = None
        self._subList = []

    def update(self, json):
        # cleanpu the instances
        self._clean_instances()
        self._json = json
        self._instanciate()

    def _instanciate(self):
        """ parse the json and load all needed components
        """
        try:
            self._parsed_condition = self.__parse_part(self._json)

            # Set the trigger to the last test of each kind of test
            # Only SensorTest class receive generic_trigger
            self._log.info(u"Scenario '{0}' : configure the trigger to the last item of each test instance".format(remove_accents(self._name)))
            for a_kind_of_test in self._test_instances:
                if a_kind_of_test.startswith("sensor.SensorTest"):
                    self._log.debug(u"Scenario '{0}' : test instance : {1} ({2} items)".format(remove_accents(self._name), a_kind_of_test, len(self._test_instances[a_kind_of_test])))
                    for idx, val in enumerate(self._test_instances[a_kind_of_test]):
                        if val.__class__.__name__ == 'SensorTest':
                            self._log.debug("Set trigger for item '{0}' to generic_trigger".format(idx))
                            val.set_trigger(self.generic_trigger)
                        else:
                            self._log.debug("Set trigger for item '{0}' to dummy".format(idx))
                            val.set_trigger(self._dummy)

            self._log.debug(u"Scenario '{0}' python generated code : \n{1}".format(remove_accents(self._name), self._parsed_condition))
            # this line is to decomment only for debug purpose
            # it will display the evaluated if conditions
            # but so, it will evaluate all sensors, so it may trigger some scenarios on startup in double
            #self._log.debug(u"Now, the python code evaluated is : \n{0}".format(self.__parse_part(self._json, debug = True)))
            tmp = ast.parse(self._parsed_condition)
            #self._compiled_condition = compile(tmp, "Scenario {0}".format(remove_accents(self._name)), 'exec')
            buf = remove_accents(self._name)
            buf = ucode(buf)
            self._compiled_condition = compile(tmp, "Scenario {0}".format(buf), 'exec')
            if len(self._subList) > 0:
                self._sub = MQAsyncSub.__init__(self, zmq.Context(), 'scenario-sensor', set(self._subList))
        except:
            raise

    def __parse_part(self, part, level=0, debug=False, parentPart=False):
        """Parse the json code and generate a python string that can be evaluated
        indentation needs to be done on the following objects:
        - do of an if part
        - else items of an if part
        - get/set variables
        If debug=False, generate the python code for the scenario
        Else, generate a python code evaluated for debugging
        If parentPart, change SensorTest as SensorValue class to avoid tiggerring not needed.
        """
        # Do not handle disabled blocks
        if 'disabled'in part and part['disabled'] == 'true':
            return None
        # build the return list
        retlist = []
        nlevel = False
        # handle the old dom_condition block
        if part['type'] == 'dom_condition':
            # Rename IF to If0
            part['IF0'] = part.pop('IF')
            # Rename DO to Do0
            part['DO0'] = part.pop('DO')
            # rename dom_condition to logic_if
            part['type'] = 'controls_if'
        # translate datatype to default blocks
        if part['type'][0:3] == 'DT_':
            # find the parent
            dt_parent = part['type']
            while 'parent' in self.datatypes[dt_parent] and self.datatypes[dt_parent]['parent'] != None:
                dt_parent = self.datatypes[dt_parent]['parent']
            # translate
            if dt_parent == "DT_Bool":
                part['type'] = "logic_boolean"
            elif dt_parent == "DT_Number":
                part['type'] = "math_number"
            elif dt_parent == "DT_DateTime":
                part['type'] = "date_time"
            elif dt_parent == "DT_String":
                part['type'] = "text"
            else:
                part['type'] = "text"
        # parse the blocks
        if part['type'] == 'controls_if':
            # handle all Ifx and dox
            incLev = 1 # Account for elif level to  indente an else if
            for ipart, val in sorted(part.items()):
                if ipart.startswith('IF'):
                    num = int(ipart.replace('IF', ''))
                    if num == 0:
                        st = "print('---- Start evaluating ----')\nif"
                        incLev = 1
                    else:
                        st =  "{0}{1}".format(pyObj(u"else:\n", num-1), pyObj(u"if", num))
                        incLev = num + 1
                    # if stays at the same lvl
                    ifp = self.__parse_part(part["IF{0}".format(num)], level, debug, False)
                    retlist.append( pyObj(u"{0} {1}:\r\n".format(st, ifp), level) )
                    # do is a level deeper
                    dop = self.__parse_part(part["DO{0}".format(num)], (level+incLev), debug, True)
                    retlist.append( pyObj(dop, level) )
            # handle ELSE
            if 'ELSE' in part:
                incLev -= 1 # decrease elif level for final else, could be 0 if no elif
                retlist.append( pyObj(u"else:\r\n", level+incLev) )
                retlist.append( pyObj(self.__parse_part(part['ELSE'], (level+incLev+1), debug, parentPart), (level)) )
        # Set a local variable
        elif part['type'] == 'variables_set':
            retlist.append( pyObj(u"{0}={1}\r\n".format(part['VAR'], self.__parse_part(part["VALUE"], level, debug, parentPart)), level) )
        # get a local variable
        elif part['type'] == 'variables_get':
            retlist.append( pyObj(u"{0} if vars().has_key('{0}') else ''".format(part['VAR']), level) )
        # True and False block
        elif part['type'] == 'logic_boolean':
            if part['BOOL'] in ("TRUE", "1", 1, True):
                retlist.append( pyObj("True") )
            else:
                retlist.append( pyObj("False") )
        # a simple static number
        elif part['type'] == 'math_number':
            retlist.append( pyObj("float(\"{0}\")".format(part['NUM'])) )
        # a date/time or timestamp
        elif part['type'] == 'date_time':
            retlist.append( pyObj("parser.parse(\"{0}\")".format(part['TEXT'])) )
        # a simple text string
        elif part['type'] == 'text':
            retlist.append( pyObj(u"\"{0}\"".format(part['TEXT'])) )
        # a block to join multiple text parts
        elif part['type'] == 'text_join':
            reslst = []
            for ipart, val in sorted(part.items()):
                if ipart.startswith('ADD'):
                    addp = self.__parse_part(part[ipart], level, debug, parentPart)
                    #reslst.append(u"str({0})".format(addp))
                    reslst.append(u"to_unicode({0})".format(addp))
            retlist.append( pyObj(u" + ".join(reslst)) )
        # get the length of a string
        elif part['type'] == 'text_length':
            retlist.append( pyObj(u"len({0})".format(self.__parse_part(part['VALUE'], level, debug, parentPart))) )
        # is the string empty
        elif part['type'] == 'text_isEmpty':
            retlist.append( pyObj(u"not len({0})".format(self.__parse_part(part['VALUE'], level, debug, parentPart))) )
        # do a calculation on 2 numbers
        elif part['type'] == 'math_arithmetic':
            if part['OP'].lower() == "add":
                compare = "+"
            elif part['OP'].lower() == "minus":
                compare = "-"
            elif part['OP'].lower() == "multiply":
                compare = "*"
            elif part['OP'].lower() == "divide":
                compare = "/"
            elif part['OP'].lower() == "power":
                compare = "^"
            retlist.append( pyObj(u"( {0} {1} {2} )".format(self.__parse_part(part['A'], level, debug, parentPart), compare, self.__parse_part(part['B'], level, debug, parentPart))) )
        # logically compare 2 items
        elif part['type'] == 'logic_compare':
            if part['OP'].lower() == "eq":
                compare = "=="
            if part['OP'].lower() == "neq":
                compare = "!="
            elif part['OP'].lower() == "lt":
                compare = "<"
            elif part['OP'].lower() == "lte":
                compare = "<="
            elif part['OP'].lower() == "gt":
                compare = ">"
            elif part['OP'].lower() == "gte":
                compare = ">="
            retlist.append( pyObj(u"( {0} {1} {2} )".format(self.__parse_part(part['A'], level, debug, parentPart), compare, self.__parse_part(part['B'], level, debug, parentPart))) )
        # logical operate (and, or, not)
        elif part['type'] == 'logic_operation':
            retlist.append( pyObj(u"( {0} {1} {2} )".format(self.__parse_part(part['A'], level, debug, parentPart), part['OP'].lower(), self.__parse_part(part['B'], level, debug, parentPart))) )
        # a not function
        elif part['type'] == 'logic_negate':
            retlist.append( pyObj(u"not {0}".format(self.__parse_part(part['BOOL'], level, debug, parentPart))) )
        # handle hysteresis
        elif part['type'] == "trigger.Hysteresis":
            test = self._create_instance(part['type'], 'test', parentPart)
            test[0].fill_parameters({"id.id": part['id']})
            if debug == False:
                retlist.append( pyObj(u"if self._mapping['test']['{0}'].evaluate():\r\n".format(test[1]), level) )
            else:
                retlist.append( eval(u"if self._mapping['test']['{0}'].evaluate():\r\n".format(test[1]), level) )
            nlevel = level
            level = level + 1
            retlist.append( pyObj(u"{0}".format(self.__parse_part(part['Run'], level, debug, parentPart))) )
        # apply an action
        elif "Action" in part['type']:
            act = self._create_instance(part['type'], 'action', parentPart)
            for p, v in part.items():
                if p not in ['id', 'type', 'NEXT']:
                    if 'type' in v:
                        v2 = ( self.__parse_part(v, 0, debug, parentPart) )
                    else:
                        v2 = u"\"{0}\"".format(v)
                    retlist.append( pyObj(u"self._mapping['action']['{0}'].set_param(\"{1}\", ({2}))\r\n".format(act[1], p, v2), level) )
            retlist.append( pyObj(u"self._mapping['action']['{0}'].do_action()\r\n".format(act[1]), level) )
        # if we end up here we should be a test case
        else:
            test = self._create_instance(part['type'], 'test', parentPart)
            # test[0] : test object
            # test[1] : test uuid

            # build a test instance list. Example :
            # foo.bar
            #  \_ obj1
            #  \_ obj2
            #  \_ obj3
            # sensor.sensorTest
            #  \_ obj1
            #  \_ obj2
            if not part['type'] in self._test_instances:
                self._test_instances[part['type']] = [test[0]]
            else:
                self._test_instances[part['type']].append(test[0])

            test[0].fill_parameters(part)
            if debug == False:
                retlist.append( pyObj(u"self._mapping['test']['{0}'].evaluate()".format(test[1])) )
            else:
                retlist.append( eval(u"self._mapping['test']['{0}'].evaluate()".format(test[1])) )
        # handle the NEXT, so we can stack blocks
        if 'NEXT'in part:
            retlist.append( pyObj(u"{0}".format(self.__parse_part(part['NEXT'], level if not nlevel else nlevel, debug, parentPart))) )
        # build the output string
        res = u""
        for ret in retlist:
            #res += u"{0}".format(str(ret))
            res += u"{0}".format(ret)
        # return the python string
        #return str(res)
        return res

    def get_parsed_condition(self):
        """Returns the parsed condition
        @return None if parse_condition as never called with a valid condition else the parsed condition
        """
        if self._parsed_condition is None:
            self._log.debug(u"get_parsed_condition called but parsed_condition is empty, try to parse condition first")
        return self._parsed_condition

    def eval_condition(self):
        """ Evaluate the condition.
        @raise ValueError if no parsed condition is avaiable
        @return a boolean representing result of evaluation
        """
        self._log.debug(u"Eval the condition!")
        if self._compiled_condition is None:
            return None
        try:
            exec(self._compiled_condition)
        except Exception as a:
            self._log.error(u"Error while evaluating condition '{0}'. Error is : {1}".format(self._compiled_condition, traceback.format_exc()))
            raise

    def on_message(self, did, msg):
        for (uid, item) in self._mapping['test'].items():
            item.on_message(did, msg)

    def _dummy(self, foo):
        """ Dummy function to avoid calling self.generic_trigger() when not needed
            See _create_instance for more details
        """
        self._log.debug(u"Dummy sensor {0} escape trigger with value : {1}".format(foo._sensorId, foo._res))

    def _create_instance(self, inst, itype, parentPart):
        uuid = self._get_uuid()
        if itype == 'test':
            # To avoid triggering a scenario N times if it uses N times the same test, we register the used tests
            # and use a dummy trigger (which does nothing) for tests 2...N and the generic_trigger for the test 1
            ### TODO : remove
            ### TODO : remove
            ### TODO : remove
            ### TODO : remove
            #if inst in self._test_instances:
            #    trigger = self._dummy
            #else:
            #    trigger = self.generic_trigger

            # default : we set the generic trigger for all. It may be changed later in the code for some kind of tests (sensorTest for example).
            trigger = self.generic_trigger
            try:
                mod, clas, param = inst.split('.')
            except ValueError as err:
                mod, clas = inst.split('.')
                param = None

            module_name = "domogik.scenario.tests.{0}".format(mod)
            if parentPart : # Parent block is a DO for action, SensorTest must be redirect to SensorValue
                # If SensorTest allready exist on IF, same Sensor stay in Test mode not Value, so a dummy became SensorTestDummy and not a SensorValueDummy.
                # This 2 class are equivalante, so finale behavior is same between SensorTestDummy and SensorValueDummy.
                if clas == 'SensorTest' : clas='SensorValue'  # force class as SensorValue to avoid trigger evaluation
            objM = None
            for i in self._mapping['test'] :
                objM = self._mapping['test'][i]
                if objM.__class__.__name__ == 'SensorTest' and objM._sensorId == param :
                    self._log.debug(u"SensorTest for sensor {0} allready set, move to dummy instance".format(param))
                    clas='SensorTestDummy' # force class as SensorTestDummy to avoid uncontrollable call order update
                    break
                elif objM.__class__.__name__ == 'SensorValue' and objM._sensorId == param :
                    self._log.debug(u"SensorValue for sensor {0} allready set, move to dummy instance".format(param))
                    clas='SensorValueDummy' # force class as SensorValueDummy to avoid uncontrollable call order update
                    break
                else :
                    objM = None
            cobj = getattr(__import__(module_name, fromlist=[mod]), clas)
            self._log.debug(u"Create test instance {0} with uuid {1}".format(inst, uuid))
            #obj = cobj(log=self._log, trigger=self.generic_trigger, cond=self, params=param)
            obj = cobj(log=self._log, trigger=trigger, cond=self, params=param)
            if objM is not None : objM.register_dummy(obj)
            self._subList = self._subList + obj.get_subMessages()
            self._mapping['test'][uuid] = obj
            return (obj, uuid)
        elif itype == 'action':
            try:
                mod, clas, params = inst.split('.')
            except ValueError as err:
                mod, clas = inst.split('.')
                params = None
            module_name = "domogik.scenario.actions.{0}".format(mod)

            cobj = getattr(__import__(module_name, fromlist=[mod]), clas)
            self._log.debug(u"Create action instance {0} with uuid {1}".format(inst, uuid))
            obj = cobj(log=self._log, params=params)
            index = u"{0}-{1}".format(len(self._mapping['action']), uuid)
            self._mapping['action'][index] = obj
            return (obj, index)

    def _get_uuid(self):
        """ Return some random uuid
        Needs to verify that the uuid is not already used
        """
        _uuid = str(uuid.uuid4())
        while _uuid in self._mapping['test'].keys() \
                or uuid in self._mapping['action'].keys():
            _uuid = str(uuid.uuid4())
        return _uuid

    def _call_actions(self):
        """ Call the needed actions for this scenario
        """
        pass

    def generic_trigger(self, test):
        #if test.get_condition():
        #    cond = test.get_condition()
        #    if cond.get_parsed_condition() is None:
        #        return
        #    st = cond.eval_condition()
        #else:
        #    test.evaluate()
        self.eval_condition()

class pyObj:
    """
    A simple object to fix the indentation in the generated python code
    """
    def __init__(self, data, lvl=None):
        self.data = data
        self.lvl = lvl

    def __repr__(self):
        """
        If lvl is set, indent that many times
        """
        ident = (u"    " * self.lvl) if self.lvl else ""
        result = [u"{0}{1}".format(ident, line) for line in self.data.splitlines(True)]
        return u"".join(result)

if __name__ == "__main__":
    import logging
    import json
    jsons = """
        {"type":"dom_condition","id":"1","IF":{"type":"textinpage.TextInPageTest","id":"5","url.urlpath":"http://cereal.sinners.be/test","url.interval":"10","text.text":"foo"},"deletable":false}
        """
    s = ScenarioInstance(logging, 10, "name", json.loads(jsons))
    print(s._parsed_condition)
    print(s._mapping)
    print(s.eval_condition())
