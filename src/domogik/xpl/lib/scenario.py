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

This plugin for RINOR manages scenarii

Implements
==========


@author: Maxence Dunnewind
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from xml.dom import minidom
import pkgutil
import importlib
import inspect
import uuid
import domogik.xpl.lib.scenario.tests as s_t
import domogik.xpl.lib.scenario.parameters as s_p
import domogik.xpl.lib.scenario.conditions as s_c
from domogik.xpl.common.plugin import XplPlugin

class ScenariosManager(XplPlugin):
    """ Manage scenarios : create them, evaluate them, etc ...
        A scenario instance contains a condition, which is a boolean combination of many tests,
        and a list of actions
        Each test can be :
         - test on the test of any device
         - test on the time
         - action triggered by user (click on UI for ex)
        The test on devices are managed directly by xpl Listeners
        The test on time will be managed by a TimeManager
        The actions will be managed by an ActionManager
    """

    def __init__(self):
        """ Create ScenarioManager instance
            @param log : Logger instance
        """
        XplPlugin.__init__(self, name = 'scenario')
        self.log.info("Scenario manager initialized") 
        self.wait()

    def get_uuid(self):
        """ Return some random uuid
        """
        return str(uuid.uuid4())

    def list_tests(self):
        """ Return the list of tests
        """
        res = {}
        tests = self.__return_list_of_classes(s_t)
        for name,cls in tests:
            inst = cls()
            res[name] = inst.get_parameters()
            inst.destroy()
        return res

    def list_conditions(self):
        """ Return the list of conditions
        """
        return self.__return_list_of_classes(s_c)

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
        for  name,cls in params:
            inst = cls()
            res[name] = inst.get_expected_entries()
            inst.destroy()
        return res

    def __return_list_of_classes(self, package):
        """ Return the list of module/classes in a package
        @param package : a reference to the package that need to be explored
        @return a list of tuple ('modulename.Classname', <instance of class>)
        """
        res = []
        mods = pkgutil.iter_modules(package.__path__)
        for module in mods:
            imported_mod = importlib.import_module('.' + module[1],package.__name__) 
            #get the list of classes in the module
            classes = [ m for m in  inspect.getmembers(imported_mod) if inspect.isclass(m[1]) ]
            # Filter in order to keep only the classes that belong to domogik package and are not abstract
            res.extend([ (module[1] + "." + c[0], c[1]) for c in filter( \
                lambda x : x[1].__module__.startswith("domogik.") and not  x[0].startswith("Abstract"), classes)])
        return res


if __name__ == "__main__":
    print "init"
    s = ScenariosManager()
    print "initialized"
    print s.list_tests()
    print s.list_conditions()
    print s.list_parameters()
    s.force_leave()
