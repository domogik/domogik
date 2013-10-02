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

This plugin manages scenarii

Implements
==========


@author: Maxence Dunnewind
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import pkgutil
import importlib
import inspect
import uuid
import json
import domogik.common.scenario.tests as s_t
import domogik.common.scenario.parameters as s_p
import domogik.common.scenario.conditions as s_c
import domogik.common.scenario.actions as s_a
from domogik.common.scenario.conditions.condition import Condition
from exceptions import KeyError


class ScenarioManager:
    """ Manage scenarios : create them, evaluate them, etc ...
        A scenario instance contains a condition, which is a boolean
        combination of many tests,
        and a list of actions
        Each test can be :
         - test on the test of any device
         - test on the time
         - action triggered by user (click on UI for ex)
        The test on devices are managed directly by xpl Listeners
        The test on time will be managed by a TimeManager
        The actions will be managed by an ActionManager
    """

    def __init__(self, log):
        """ Create ScenarioManager instance
            @param log : Logger instance
        """
        # Keep uuid <-> instance mapping for tests and actions
        self._tests_mapping = {}
        self._actions_mapping = {}
        # Keep list of conditions as name : instance
        self._conditions = {}
        # Keep list of actions uuid linked to a condition  as name : [uuid1, uuid2, ... ]
        self._conditions_actions = {}
        self.log = log

    def __ask_instance(self, obj, mapping):
        """ Generate an uuid corresponding to the object passed as parameter
        @param obj : a string as "objectmodule.objectClass" to instanciate
        @return an uuid referencing a new instance of the object
        """
        _uuid = self.get_uuid()
        mapping[_uuid] = obj
        return _uuid

    def ask_test_instance(self, obj):
        """ Generate an uuid corresponding to the object passed as parameter
        @param obj : a string as "objectmodule.objectClass" to instanciate
        @return an uuid referencing a new instance of the object
        """
        return self.__ask_instance(obj, self._tests_mapping)

    def ask_action_instance(self, obj):
        """ Generate an uuid corresponding to the object passed as parameter
        @param obj : a string as "objectmodule.objectClass" to instanciate
        @return an uuid referencing a new instance of the object
        """
        return self.__ask_instance(obj, self._actions_mapping)

    def __instanciate(self):
        """ This method will read the list of uuids, and create coresponding
        instances if they don't exist yet.
        """
        for _uuid in self._tests_mapping:
            inst = self._tests_mapping[_uuid]
            if type(inst) in [str, unicode]:
                # _test_cache keeps a list of classname/class object
                # so we have to load the module/class etc ... only once
                if inst not in self._test_cache:
                    mod, clas = inst.split('.')
                    module_name = "domogik.common.scenario.tests.%s" % mod
                    cobj = getattr(__import__(module_name, fromlist=[mod]), clas)
                    self._test_cache[inst] = cobj
                    self.log.debug("Add class %s to test cache" % inst)
                self.log.debug("Create instance for uuid %s" % _uuid)
                self._tests_mapping[_uuid] = self._test_cache[inst](self.log, trigger=self.generic_trigger)
        for _uuid in self._actions_mapping:
            inst = self._actions_mapping[_uuid]
            if type(inst) in [str, unicode]:
                # _action_cache keeps a list of classname/class object
                # so we have to load the module/class etc ... only once
                if inst not in self._action_cache:
                    mod, clas = inst.split('.')
                    module_name = "domogik.common.scenario.actions.%s" % mod
                    cobj = getattr(__import__(module_name, fromlist=[mod]), clas)
                    self._action_cache[inst] = cobj
                    self.log.debug("Add class %s to action cache" % inst)
                self.log.debug("Create action instance for uuid %s" % _uuid)
                self._actions_mapping[_uuid] = self._action_cache[inst](self.log, trigger=self.generic_trigger)

    def shutdown(self):
        """ Callback to shut down all parameters
        """
        for _uuid in self._tests_mapping:
            inst = self._mapping[uuid]
            if type(inst) not in [str, unicode]:
                self.log.info("Destroy test %s with uuid %s" % (inst.__class__, _uuid))
                inst.destroy()

    def generic_trigger(self, test_i):
        """ Generic trigger to refresh a condition state when some value change
        @todo allow custom triggers
        @param test_i the test instance
        """
        if test_i.get_condition():
            cond = test_i.get_condition()
            if cond.get_parsed_condition is None:
                return
            st = cond.eval_condition()
            test_i._log.info("state of condition '%s' is %s" % (cond.get_parsed_condition(), st))
        else:  # We have no condition, just evaluate test
            test_i.evaluate()

    def get_parsed_condition(self, name):
        """ Call cond.get_parsed_condition on the cond with name 'name'
        @param name : name of the Condition
        @return {'name':name, 'data': parsed_condition} or raise Exception
        """
        if name not in self._conditions:
            raise KeyError('no key %s in conditions table' % name)
        else:
            parsed = self._conditions[name].get_parsed_condition()
            return {'name': name, 'data': parsed}

    def get_uuid(self):
        """ Return some random uuid
        """
        return str(uuid.uuid4())

    def create_condition(self, name, json_input):
        """ Create a Condition instance from the provided json.
        @param name : A name for the condition instance
        @param json_input : JSON representation of the condition
        The JSON will be parsed to get all the uuids, and test instances will be created.
        @Return {'name': name} or raise exception
        """
        try:
            payload = json.loads(json_input)  # quick test to check if json is valid
        except:
            self.log.error("Invalid json : %s" % json_input)
            return None
        try:
            self._test_cache = {}
            self._action_cache = {}
            self.__instanciate()
            c = Condition(self.log, json_input, self._tests_mapping)
            self._conditions[name] = c
            self.log.debug("Create condition %s with payload %s" % (name, payload))
            return {'name': name}
        except Exception, e:
            self.log.error("Error during condition create")
            raise e

    def eval_condition(self, name):
        """ Evaluate a condition calling eval_condition from Condition instance
        @param name : The name of the condition instance
        @return {'name':name, 'result': evaluation result} or raise Exception
        """
        if name not in self._conditions:
            raise KeyError('no key %s in conditions table' % name)
        else:
            res = self._conditions[name].eval_condition()
            return {'name': name, 'result': res}

    def list_actions(self):
        """ Return the list of actions
        @return a hash of hashes for the different actions
        { "module1.Action1" : {
            "description" : "some description of the action",
            "parameters" : { "param1" : {
                ... see get_expected_entries for details
            }
        }
        """

        res = {}
        actions = self.__return_list_of_classes(s_a)
        for name, cls in actions:
            inst = cls()
            res[name] = {"parameters": inst.get_expected_entries(),
                         "description": inst.get_description()}
        return json.dumps(res)

    def list_tests(self):
        """ Return the list of tests
        @return a hash of hashes for the different tests
        { "module1.Test1" : {
            "description" : "some description of the test",
            "parameters" : { "param1" : {
                ... see list_parameters doc for detail on this part
            }
        }
        """

        res = {}
        tests = self.__return_list_of_classes(s_t)
        for name, cls in tests:
            inst = cls()
            res[name] = {"parameters": inst.get_parameters(),
                         "description": inst.get_description()}
            inst.destroy()
        return json.dumps(res)

    def list_conditions(self):
        """ Return the list of conditions as JSON
        """

        classes = self.__return_list_of_classes(s_c)
        res = []
        for c in classes:
            res.append(c[0])
        return json.dumps(res)

    def list_parameters(self):
        """ Return the list of parameters as JSON
        @return a hash of hash for parameters, like :
        { "module1.Parameter1" : {
                "token1": {
                    "type" : "type of token",
                    "description": "Description of token",
                    "default" : "default value or empty",
                    "values" : [ "list","of","value","that","user","can","choose"],
                    "filters" : [ "list","of","filters","or",""]
                },
                "token2" : { ... }
            }
            "module2.Parameter1" : { ... }
        }
        """
        res = {}
        params = self.__return_list_of_classes(s_p)
        for name, cls in params:
            inst = cls()
            res[name] = inst.get_expected_entries()
            inst.destroy()
        return json.dumps(res)

    def __return_list_of_classes(self, package):
        """ Return the list of module/classes in a package
        @param package : a reference to the package that need to be explored
        @return a list of tuple ('modulename.Classname', <instance of class>)
        """
        res = []
        mods = pkgutil.iter_modules(package.__path__)
        for module in mods:
            imported_mod = importlib.import_module('.' + module[1], package.__name__)
            #get the list of classes in the module
            classes = [m for m in inspect.getmembers(imported_mod) if inspect.isclass(m[1])]
            # Filter in order to keep only the classes that belong to domogik package and are not abstract
            res.extend([(module[1] + "." + c[0], c[1]) for c in filter(
                lambda x: x[1].__module__.startswith("domogik.") and not x[0].startswith("Abstract"), classes)])
        return res


if __name__ == "__main__":
    import logging
    s = ScenarioManager(logging)
    print "==== list of conditions ===="
    print s.list_conditions()
    print "==== list of parameters ===="
    print s.list_parameters()

    print "\n==== Create condition ====\n"
    print "  * get list of tests as json:"
    t = s.list_tests()
    print t
    tests = json.loads(t)
    print "  * Create a test instance of %s (%s)" % (tests.keys()[0], tests.values()[0]["description"])
    uid = s.ask_test_instance(tests.keys()[0])
    print "  * asked for an instance of %s, got uuid %s" % (tests.keys()[0], uid)
    print "  * listing parameters needed by the test :"
    test_data = tests["textinpage.TextInPageTest"]
    for k in test_data["parameters"]:
        v = test_data["parameters"][k]
        print "    - %s" % k
        print "      > type : %s" % v["type"]
        print "      > expected tokens :"
        for tok in v["expected"]:
            vtok = v["expected"][tok]
            print "        * %s :" % tok
            print "          - default : %s" % vtok["default"]
            print "          - values : %s" % vtok["values"]
            print "          - type : %s" % vtok["type"]
            print "          - description : %s" % vtok["description"]
            print "          - filters : %s" % vtok["filters"]
    print "  * Generating JSON with values :"
    print "    - url.urlpath = http://www.google.fr"
    print "    - url.interval = 5"
    print "    - text.text = sometext"
    src = """{ "NOT" : { "%s" : {
            "url": {
                "urlpath": "http://www.google.fr",
                "interval" : "5"
            },
            "text": {
                "text": "sometext"
            }
        }
    }}""" % uid
    print "  * JSON is : %s" % json.dumps(src)
    p = json.loads(json.dumps(src))
    print p
    print "  * Create condition 'foo' with previous payload"
    c = s.create_condition("foo", json.dumps(src))
    print "    - condition created : %s" % c
    print "    - parse condition"
    c.parse_condition()
    print "    - generated condition is : %s" % c.get_parsed_condition()
    print "    - evaluate the condition, result is %s" % c.eval_condition()
    s.shutdown()
    print "  - call force_leave to stop."
