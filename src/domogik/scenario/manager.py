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
import domogik.scenario.tests as s_t
import domogik.scenario.parameters as s_p
import domogik.scenario.actions as s_a
from domogik.common.database import DbHelper
from domogik.scenario.scenario import ScenarioInstance
try:
    from exceptions import KeyError
except:
    pass
import traceback
import time

DATABASE_CONNECTION_NUM_TRY = 50
DATABASE_CONNECTION_WAIT = 30



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
        # Keep list of conditions as name : instance
        self._instances = {}
        # an instance of the logger
        self.log = log
        # load all scenarios from the DB
        self._db = DbHelper()
        self.load_scenarios()

    def load_scenarios(self):
        """ Loads all scenarios from the db
        for each scenario call the create_scenario method
        """
        try:
            with self._db.session_scope():
                ### TEST if database is up
                # TODO : move in a function and use it (also used in dbmgr)
                nb_test = 0
                db_ok = False
                while not db_ok and nb_test < DATABASE_CONNECTION_NUM_TRY:
                    nb_test += 1
                    try:
                        self._db.list_user_accounts()
                        db_ok = True
                    except:
                        msg = "The database is not responding. Check your configuration of if the database is up. Test {0}/{1}. The error while trying to connect to the database is : {2}".format(nb_test, DATABASE_CONNECTION_NUM_TRY, traceback.format_exc())
                        self.log.error(msg)
                        msg = "Waiting for {0} seconds".format(DATABASE_CONNECTION_WAIT)
                        self.log.info(msg)
                        time.sleep(DATABASE_CONNECTION_WAIT)
    
                if nb_test >= DATABASE_CONNECTION_NUM_TRY:
                    msg = "Exiting dbmgr!"
                    self.log.error(msg)
                    self.force_leave()
                    return
    
                ### Do the stuff
                msg = "Connected to the database"
                self.log.info(msg)
                for scenario in self._db.list_scenario():
                    self.create_scenario(scenario.name, scenario.json, int(scenario.id), scenario.disabled, scenario.description, scenario.state)
        except:
            self.log.error(u"Error while loading the scenarios! The error is : {0}".format(traceback.format_exc()))

    def shutdown(self):
        """ Callback to shut down all parameters
        """
        for cond in self._conditions.keys():
            self.delete_scenario(cond, db_delete=False)

    def get_parsed_condition(self, name):
        """ Call cond.get_parsed_condition on the cond with name 'name'
        @param name : name of the Condition
        @return {'name':name, 'data': parsed_condition} or raise Exception
        """
        if name not in self._conditions:
            raise KeyError('no key {0} in conditions table'.format(name))
        else:
            parsed = self._conditions[name].get_parsed_condition()
            return {'name': name, 'data': parsed}

    def update_scenario(self, cid, name, json_input, dis, desc):
        cid = int(cid)
        # TODO get the current state and store it
        state = True
        if cid != 0:
            self.del_scenario(cid, False)
        return self.create_scenario(name, json_input, cid, dis, desc, state, True)

    def del_scenario(self, cid, doDB=True):
        try:
            cid = int(cid)
            if cid == 0 or cid not in self._instances.keys():
                self.log.info(u"Scenario deletion : id '{0}' doesn't exist".format(cid))
                return {'status': 'ERROR', 'msg': u"Scenario {0} doesn't exist".format(cid)}
            else:
                self._instances[cid]['instance'].destroy()
                del(self._instances[cid])
                if doDB:
                    with self._db.session_scope():
                        self._db.del_scenario(cid)
                self.log.info(u"Scenario {0} deleted".format(cid))
        except:
            msg = u"Error while deleting the scenario id='{0}'. Error is : {1}".format(cid, traceback.format_exc())
            self.log.error(msg)
            return {'status': 'ERROR', 'msg': msg}

    def create_scenario(self, name, json_input, cid=0, dis=False, desc=None, state=False, update=False):
        """ Create a Scenario from the provided json.
        @param name : A name for the condition instance
        @param json_input : JSON representation of the condition
        The JSON will be parsed to get all the uuids, and test instances will be created.
        The json needs to have 2 keys:
            - condition => the json that will be used to create the condition instance
            - actions => the json that will be used for creating the actions instances
        @Return {'name': name} or raise exception
        """
        ocid = cid
        try:
            self.log.info(u"Create or save scenario : name = '{1}', id = '{1}', json = '{2}'".format(name, cid, json_input))
            payload = json.loads(json_input)  # quick test to check if json is valid
        except Exception as e:
            self.log.error(u"Creation of a scenario failed, invallid json: {0}".format(json_input))
            self.log.error(u"Error is : {0}".format(tracebeck.format_exc()))
            return {'status': 'ERROR', 'msg': 'invallid json'}

        #if 'IF' not in payload.keys():
        #        or 'DO' not in payload.keys():
        #    msg = u"the json for the scenario does not contain condition or actions for scenario {0}".format(name)
        #    self.log.error(msg)
        #    return {'status': 'ERROR', 'msg': msg}
        # db storage
        if int(ocid) == 0:
            with self._db.session_scope():
                scen = self._db.add_scenario(name, json_input, dis, desc, False)
                cid = scen.id
        elif update:
            with self._db.session_scope():
                self._db.update_scenario(cid, name, json_input, dis, desc)

        # create the condition itself
        try:
            scen = ScenarioInstance(self.log, cid, name, payload, dis, state, self._db)
            self._instances[cid] = {'name': name, 'json': payload, 'instance': scen, 'disabled': dis } 
            self.log.debug(u"Create scenario instance {0} with payload {1}".format(name, payload))
            self._instances[cid]['instance'].eval_condition()
        except Exception as e:  
            if int(ocid) == 0:
                with self._db.session_scope():
                    self._db.del_scenario(cid)
            self.log.error(u"Creation of a scenario failed. Error is : {0}".format(traceback.format_exc()))
            return {'status': 'ERROR', 'msg': 'Creation of scenario failed'}
        # return
        return {'name': name, 'status': 'OK', 'cid': cid}

    def eval_condition(self, name):
        """ Evaluate a condition calling eval_condition from Condition instance
        @param name : The name of the condition instance
        @return {'name':name, 'result': evaluation result} or raise Exception
        """
        if name not in self._conditions:
            raise KeyError('no key {0} in conditions table'.format(name))
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

        self.log.debug("ScenarioManager : list actions")
        res = {}
        actions = self.__return_list_of_classes(s_a)
        for name, cls in actions:
            if 'abstract' not in name.lower():
                self.log.debug("- {0}".format(name))
                inst = cls()
                res[name] = {"parameters": inst.get_expected_entries(),
                             "description": inst.get_description()}
        return res

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

        self.log.debug("ScenarioManager : list tests")
        res = {}
        tests = self.__return_list_of_classes(s_t)

        for name, cls in tests:
            if 'abstract' not in name.lower():
                self.log.debug("- {0}".format(name))
                inst = cls(log = self.log)

                params = []
                for p, i in inst.get_parameters().items():
                    for param, info in i['expected'].items():
                        params.append({
                                "name": "{0}.{1}".format(p, param),
                                "description": info['description'],
                                "type": info['type'],
                                "values": info['values'],
                                "filters": info['filters'],
                            })

                res[name] = {"parameters": params,
                             "blockly": inst.get_blockly(),
                             "description": inst.get_description()}
        return res

    def list_conditions(self):
        """ Return the list of conditions as JSON
        """
        ret = []
        for cid, inst in self._instances.items():
            ret.append({'cid': cid, 'name': inst['name'], 'json': inst['json'], 'disabled': inst['disabled']})
        return ret

    def enable_scenario(self, cid):
        try:
            if cid == '' or int(cid) not in self._instances.keys():
                self.log.info(u"Scenario enable : id '{0}' doesn't exist".format(cid))
                return {'status': 'ERROR', 'msg': u"Scenario {0} doesn't exist".format(cid)}
            else:
                if self._instances[int(cid)]['instance'].enable():
                    self._instances[int(cid)]['disabled'] = False
                    with self._db.session_scope():
                        self._db.update_scenario(cid, disabled=False)
                    self.log.info(u"Scenario {0} enabled".format(cid))
                    return {'status': 'OK', 'msg': u"Scenario {0} enabled".format(cid)}
                else:
                    self.log.info(u"Scenario {0} already enabled".format(cid))
                    return {'status': 'ERROR', 'msg': u"Scenario {0} already enabled".format(cid)}
        except:
            msg = u"Error while enabling the scenario id='{0}'. Error is : {1}".format(cid, traceback.format_exc())
            self.log.error(msg)
            return {'status': 'ERROR', 'msg': msg}
 
    def disable_scenario(self, cid):
        try:
            if cid == '' or int(cid) not in self._instances.keys():
                self.log.info(u"Scenario disable : id '{0}' doesn't exist".format(cid))
                return {'status': 'ERROR', 'msg': u"Scenario {0} doesn't exist".format(cid)}
            else:
                if self._instances[int(cid)]['instance'].disable():
                    self._instances[int(cid)]['disabled'] = True
                    with self._db.session_scope():
                        self._db.update_scenario(cid, disabled=True)
                    self.log.info(u"Scenario {0} disabled".format(cid))
                    return {'status': 'OK', 'msg': u"Scenario {0} disabled".format(cid)}
                else:
                    self.log.info(u"Scenario {0} already disabled".format(cid))
                    return {'status': 'ERROR', 'msg': u"Scenario {0} already disabled".format(cid)}
        except:
            msg = u"Error while disabling the scenario id='{0}'. Error is : {1}".format(cid, traceback.format_exc())
            self.log.error(msg)
            return {'status': 'ERROR', 'msg': msg}

    def test_scenario(self, cid):
        try:
            if cid == '' or int(cid) not in self._instances.keys():
                self.log.info(u"Scenario test : id '{0}' doesn't exist".format(cid))
                return {'status': 'ERROR', 'msg': u"Scenario {0} doesn't exist".format(cid)}
            else:
                self._instances[int(cid)]['instance'].test_actions()
                self.log.info(u"Scenario {0} actions called".format(cid))
                return {'status': 'OK', 'msg': u"Scenario {0} actions called".format(cid)}
        except:
            msg = u"Error while calling actions for scenario id='{0}'. Error is : {1}".format(cid, traceback.format_exc())
            self.log.error(msg)
            return {'status': 'ERROR', 'msg': msg}

    def __return_list_of_classes(self, package):
        """ Return the list of module/classes in a package
        @param package : a reference to the package that need to be explored
        @return a list of tuple ('modulename.Classname', <instance of class>)
        """
        self.log.debug("Get list of classes for package : {0}".format(package))
        res = []
        mods = pkgutil.iter_modules(package.__path__)
        for module in mods:
            self.log.debug("- {0}".format(module))
            imported_mod = importlib.import_module('.' + module[1], package.__name__)
            #get the list of classes in the module
            classes = [m for m in inspect.getmembers(imported_mod) if inspect.isclass(m[1])]
            # Filter in order to keep only the classes that belong to domogik package and are not abstract
            res.extend([(module[1] + "." + c[0], c[1]) for c in filter(
                lambda x: x[1].__module__.startswith("domogik.scenario.") and not x[0].startswith("Abstract"), classes)])
        return res


if __name__ == "__main__":
    import logging
    s = ScenarioManager(logging)
    print("==== list of actions ====")
    print(s.list_actions())
    print("==== list of tests ====")
    print(s.list_tests())

    print("\n==== Create condition ====\n")
    jsons = """
            {"type":"dom_condition","id":"1","IF":{"type":"textinpage.TextInPageTest","id":"5","url.urlpath":"http://cereal.sinners.be/test","url.interval":"10","text.text":"foo"},"deletable":false, "DO":{} }
                    """
    c = s.create_scenario("name", jsons)
    print("    - condition created : {0}".format(c))
    print("    - list of instances : {0}".format(s.list_conditions()))
