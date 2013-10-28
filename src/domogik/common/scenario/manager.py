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
from domogik.common.database import DbHelper
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
        { 
         "condition" :
            { "AND" : {
                    "OR" : {
                        "one-uuid" : {
                            "param_name_1" : {
                                "token1" : "value",
                                "token2" : "othervalue"
                            },
                            "param_name_2" : {
                                "token3" : "foo"
                            }
                        },
                        "another-uuid" : {
                            "param_name_1" : {
                                "token4" : "bar"
                            }
                        }
                    },
                    "yet-another-uuid" : {
                        "param_name_1" : {
                            "url" : "http://google.fr",
                            "interval" : "5"
                        }
                    }
                }
            },
         "actions" : [
            "uid-for-action" : {
                "param1" : "value1",
                "param2" : "value2"
            },
            "uid-for-action2" : {
                "param3" : "value3"
            }
         ]
        }
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
        # an instance of the logger
        self.log = log
        # As we lazy-load all the tests/actions in __instanciate
        # we need to keep the module in a list so that we don't need to reload them
        # every time.
        self._test_cache = {}
        self._action_cache = {}
        # load all scenarios from the DB
        self._db = DbHelper()
        self.load_scenarios()

    def load_scenarios(self):
        """ Loads all scenarios from the db
        for each scenario call the create_scenario method
        """
        with self._db.session_scope():
            for scenario in self._db.list_scenario():
                # add all uuids to the mappings
                for uid in scenario.uuids:
                    if uid.is_test:
                        self.__ask_instance(uid.key, self._tests_mapping, uid.uuid)
                    else:
                        self.__ask_instance(uid.key, self._actions_mapping, uid.uuid)
                # now all uuids are created go and install the condition
                self.create_scenario(scenario.name, scenario.json, store=False)

    def __ask_instance(self, obj, mapping, set_uuid=None):
        """ Generate an uuid corresponding to the object passed as parameter
        @param obj : a string as "objectmodule.objectClass" to instanciate
        @param mapping : in what map to store the new uuid
        @param uuid : if the uuid is provided, don't generate it
        @return an uuid referencing a new instance of the object
        """
        if set_uuid is None:
            _uuid = self.get_uuid()
        else:
            _uuid = set_uuid
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
        If they don't exist yet the type of the instans is str or unicode
        """
        for _uuid in self._tests_mapping:
            inst = self._tests_mapping[_uuid]
            if type(inst) in [str, unicode]:
                # _test_cache keeps a list of classname/class object
                # so we have to load the module/class etc ... only once
                if inst not in self._test_cache:
                    mod, clas = inst.split('.')
                    module_name = "domogik.common.scenario.tests.{0}".format(mod)
                    cobj = getattr(__import__(module_name, fromlist=[mod]), clas)
                    self._test_cache[inst] = cobj
                    self.log.debug(u"Add class {0} to test cache".format(inst))
                self.log.debug(u"Create test instance {0} with uuid {1}".format(inst, _uuid))
                self._tests_mapping[_uuid] = self._test_cache[inst](self.log, trigger=self.generic_trigger)
        for _uuid in self._actions_mapping:
            inst = self._actions_mapping[_uuid]
            if type(inst) in [str, unicode]:
                # _action_cache keeps a list of classname/class object
                # so we have to load the module/class etc ... only once
                if inst not in self._action_cache:
                    mod, clas = inst.split('.')
                    module_name = "domogik.common.scenario.actions.{0}".format(mod)
                    cobj = getattr(__import__(module_name, fromlist=[mod]), clas)
                    self._action_cache[inst] = cobj
                    self.log.debug(u"Add class {0} to action cache".format(inst))
                self.log.debug(u"Create action instance {0} with uuid {1}".format(inst, _uuid))
                self._actions_mapping[_uuid] = self._action_cache[inst](self.log)

    def shutdown(self):
        """ Callback to shut down all parameters
        """
        for _uuid in self._tests_mapping:
            inst = self._mapping[uuid]
            if type(inst) not in [str, unicode]:
                self.log.info(u"Destroy test %s with uuid %s" % (inst.__class__, _uuid))
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
        Needs to verify that the uuid is not already used
        Does this in the mappings (for actions and tests)
        """
        _uuid = str(uuid.uuid4())
        while _uuid in self._tests_mapping.keys() \
                or uuid in self._actions_mapping.keys():
            _uuid = str(uuid.uuid4())
        return _uuid

    def create_scenario(self, name, json_input, store=True):
        """ Create a Scenario from the provided json.
        @param name : A name for the condition instance
        @param json_input : JSON representation of the condition
        The JSON will be parsed to get all the uuids, and test instances will be created.
        The json needs to have 2 keys:
            - condition => the json that will be used to create the condition instance
            - actions => the json that will be used for creating the actions instances
        @Return {'name': name} or raise exception
        """
        try:
            payload = json.loads(json_input)  # quick test to check if json is valid
        except Exception as e:
            print e
            self.log.error(u"Invalid json : {0}".format(json_input))
            return None
        if 'condition' not in payload.keys() \
                or 'actions' not in payload.keys():
            raise KeyError(u"the json for the scenario does not contain condition or actions for scenario {0}".format(name))
        # instantiate all objects
        self.__instanciate()
        # create the condition itself
        c = Condition(self.log, name, json.dumps(payload['condition']), self._tests_mapping, self.trigger_actions)
        self._conditions[name] = c
        self._conditions_actions[name] = []
        self.log.debug(u"Create condition {0} with payload {1}".format(name, payload['condition']))
        # build a list of actions
        for action in payload['actions'].keys():
            # action is now a tuple
            #   (uid, params)
            self._conditions_actions[name].append(action) 
            self._actions_mapping[action].do_init(payload['actions'][action]) 
 
        # store the scenario in the db
        if store:
            with self._db.session_scope():
                # store the scenario
                scen = self._db.add_scenario(name, json_input)
                # store the tests
                for uuid in c.get_mapping():
                    cls = str(self._tests_mapping[uuid].__class__).replace('domogik.common.scenario.tests.', '')
                    self._db.add_scenario_uuid(scen.id, uuid, cls, 1)
                # store the actions
                for uuid in self._conditions_actions[name]:
                    cls = str(self._actions_mapping[uuid].__class__).replace('domogik.common.scenario.actions.', '')
                    self._db.add_scenario_uuid(scen.id, uuid, cls, 0)
        else:
            c.parse_condition()
        # return
        return {'name': name}

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

    def trigger_actions(self, name):
        """ Trigger that will be called when a condition evaluates to True
        """
        if name not in self._conditions_actions \
                or name not in self._conditions:
            raise KeyError('no key %s in one of the _conditions tables table' % name)
        else:
            for action in self._conditions_actions[name]:
                self._actions_mapping[action].do_action( \
                        self._conditions[name], \
                        self._conditions[name].get_mapping() \
                        )

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
                lambda x: x[1].__module__.startswith("domogik.common.scenario.") and not x[0].startswith("Abstract"), classes)])
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
