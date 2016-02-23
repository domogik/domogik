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
from exceptions import ValueError
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
import zmq
import traceback

class ScenarioInstance:
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

    def __init__(self, log, dbid, name, json, disabled):
        """ Create the instance
        @param log : A logger instance
        @param dbid : The id of this scenario in the db
        @param json : The json describing the scenario
        """
        self._log = log
        self._name = name
        self._json = json
        self._disabled = disabled

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

    def destroy(self):
        """ Cleanup the class
        """
        self._clean_instances()

    def _clean_instances(self):
        for (uid, item) in self._mapping['action'].items():
            item.destroy()
        self._mapping['action'] = {}
        for (uid, item) in self._mapping['test'].items():
            item.destroy()
        self._mapping['test'] = {}

    def update(self, json):
        # cleanpu the instances
        self._clean_instances()
        self._json = json
        self._instanciate()

    def _instanciate(self):
        """ parse the json and load all needed components
        """
        ## get the datatypes
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('datatype.get')
        res = cli.request('manager', msg.get(), timeout=10)
        datatypes = None
        if res is not None:
            res = res.get_data()
            if 'datatypes' in res:
                datatypes = res['datatypes']
        try:
            # step 1 parse the "do" part
            self.__parse_do_part(self._json['DO'])
            # step 2 parse the "if" part        
            self._parsed_condition = self.__parse_if_part(self._json['IF'], datatypes)
        except:
            raise

    def __parse_if_part(self, part, datatypes = None):
        # translate datatype to default blocks
        if part['type'][0:3] == 'DT_':
            # find the parent
            dt_parent = part['type']
            while 'parent' in datatypes[dt_parent] and datatypes[dt_parent]['parent'] != None:
                dt_parent = datatypes[dt_parent]['parent']
            # translate
            print("PARENT={0}".format(dt_parent))
            if dt_parent == "DT_Bool":
                part['type'] = "logic_boolean"
            elif dt_parent == "DT_Number":
                part['type'] = "math_number"
            elif dt_parent == "DT_String":
                part['type'] = "text"
        # parse it
        if part['type'] == 'logic_boolean':
            if part['BOOL'] in ("TRUE", "1", 1, True):
                return "\"1\""
            else:
                return "\"0\""
        elif part['type'] == 'math_number':
            return "float(\"{0}\")".format(part['NUM'])
        elif part['type'] == 'text':
            return "\"{0}\"".format(part['TEXT'])
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
            return "( {0} {1} {2} )".format(self.__parse_if_part(part['A'], datatypes), compare, self.__parse_if_part(part['B'], datatypes))
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
            return "( {0} {1} {2} )".format(self.__parse_if_part(part['A'], datatypes), compare, self.__parse_if_part(part['B'], datatypes))
        elif part['type'] == 'logic_operation':
            return "( {0} {1} {2} )".format(self.__parse_if_part(part['A'], datatypes), part['OP'].lower(), self.__parse_if_part(part['B'], datatypes))
        elif part['type'] == 'logic_negate':
            return "not {0}".format(self.__parse_if_part(part['BOOL']))
        else:
            test = self._create_instance(part['type'], 'test')
            test[0].fill_parameters(part)
            return "self._mapping['test']['{0}'].evaluate()".format(test[1])

    def __parse_do_part(self, part):
        action = self._create_instance(part['type'], 'action')
        action[0].do_init(part)
        if 'NEXT' in part:
            self.__parse_do_part(part['NEXT'])

    def get_parsed_condition(self):
        """Returns the parsed condition
        @return None if parse_condition as never called with a valid condition else the parsed condition
        """
        if self._parsed_condition is None:
            self._log.debug("get_parsed_condition called but parsed_condition is empty, try to parse condition first")
        return self._parsed_condition

    def eval_condition(self):
        """ Evaluate the condition.
        @raise ValueError if no parsed condition is avaiable
        @return a boolean representing result of evaluation
        """
        if self._parsed_condition is None:
            return None
        res = eval(self._parsed_condition)
        self._log.debug("_parsed condition is : {0}, eval is {1}".format(self._parsed_condition, eval(self._parsed_condition)))
        if res:
            return True
        else:
            return False

    def _create_instance(self, inst, itype):
        uuid = self._get_uuid()
        if itype == 'test':
            try:
                print(inst)
                mod, clas, param = inst.split('.')
            except ValueError as err:
                mod, clas = inst.split('.')
                param = None
            module_name = "domogik.scenario.tests.{0}".format(mod)
            cobj = getattr(__import__(module_name, fromlist=[mod]), clas)
            self._log.debug(u"Create test instance {0} with uuid {1}".format(inst, uuid))
            obj = cobj(log=self._log, trigger=self.generic_trigger, cond=self, params=param)
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
            index = "{0}-{1}".format(len(self._mapping['action']), uuid)
            self._mapping['action'][index] = obj
            return (obj, uuid)

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
        local_vars = {"foo" : "bar"}
        self._log.debug("CALLING actions. Local vars = '{0}'".format(local_vars))
        idx = 0
        for act in sorted(self._mapping['action']):
            idx += 1
            try:
                self._log.debug("Before action n°{0}. Local vars = '{1}'".format(idx, local_vars))
                self._mapping['action'][act].do_action(local_vars)
                self._log.debug("After action n°{0}. Local vars = '{1}'".format(idx, local_vars))
            except:
                self._log.error("Error while executing action : {0}".format(traceback.format_exc()))
        self._log.debug("END CALLING actions")

    def generic_trigger(self, test):
        if test.get_condition():
            cond = test.get_condition()
            if cond.get_parsed_condition() is None:
                return
            st = cond.eval_condition()
            self._log.info(u"Condition {0} evaluated to {1}".format(self._name, st))
            if st:
                self._call_actions()
        else:
            test.evaluate()

    def test_actions(self):
        self._call_actions()


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
