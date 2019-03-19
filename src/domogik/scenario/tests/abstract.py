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
try:
    from exceptions import IndexError, NotImplementedError, AttributeError
except:
    pass

class AbstractTest:
    """ This class provides base methods for the scenario tests
    It must not be instanciated directly but need to be extended
    A test contains :
     - A certain number of parameters. Each parameter can be :
       * A device entry
       * An operator entry
       * A "text" entry
       * A date entry
       * Any Other things if corresponding parameter is available
     - A set_parameters method to fill parameters with the value chosen by user
     - An evaluate method which do something with parameters, custom code, etc ... and return a boolean, or raise a CantEvaluate
       exception if the method can't be evaluated
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        """ Create the instance
        @param log : A logger instance
        @param trigger : a method to call when a parameter changes
        @param cond : The condition instance test is attached to
        """
        self.log = log
        self._trigger = trigger
        self._parameters = {}
        self._description = None
        self._cond = cond
        self._params = params
        self._subMessages = []
        self._outputCheck = []

    def get_subMessages(self):
        return self._subMessages

    def set_trigger(self, trigger):
        """ Update the trigger callback
        """
        self._trigger = trigger

    def set_description(self, description):
        """ Update the description of the test
        This description will be usefull to help user to understand what the test does
        @param description : A short text to describe what the test does
        """
        self._description = description

    def get_description(self):
        """ Return the current description
        @return the current description, "" if the description is empty
        """
        if not self._description:
            return ""
        return self._description

    def set_outputCheck(self, output):
        """ Update the output compatibility of the test
        Empty or None assume compatibilty of all.
        @param output : Array of list of output compatibility with other blockly
        """
        self._outputCheck = output

    def get_outputCheck(self):
        """ Return the output compatibility of the test
        @return the current output list, "null" if is empty or None
        """
        if not self._outputCheck or self._outputCheck == "null":
            return "null"
        return self._outputCheck

    def set_condition(self, cond):
        """ Set the condition where this test belongs to
        @param cond : the condition_name
        """
        self._cond = cond

    def get_condition(self):
        """ Return condition this test belongs to
        @return None if the test is not attached  to any condition (shouldn't happen out of tests)
        else return condition instance
        """
        return self._cond

    def cb_trigger(self, param):
        """ Callback called by a parameter when the fill() method is called
        Basically, it only calls the underlying ttrigger if exists
        """
        self.log.debug("Trigger {0} called by parameter {1}".format(self._trigger, param))
        if self._trigger != None:
            self._trigger(self)

    def get_raw_parameters(self):
        """ access internal parameters list
        """
        return self._parameters

    def get_parameters(self):
        """ Provide the list of parameters of the test
        The method will return a list of parameters. Each parameter is a dictionnary with as keys:
             - name : name of parameter, can be any string
         and as value another dictionnary with :
             - type : a string which describes the type, ex : "device", "operator", "time"
             - filter : dictionnary of filters to apply (ex : a technology or an housecode for device, a month for time, etc ...)
             - list_of_values : a list of possible values (for "text" entries)
             - default : default value
             - expected: list of expected keys
        Those values are mostly informational and allow the UI to create different forms
        """
        self.log.debug("Get parameters for the test")
        result = {}

        for name in self._parameters:
            self.log.debug("Parameter : {0}".format(name))
            p = self._parameters[name]
            result[name] = {
                "type": p.get_type(),
                "filter": p.get_filters(),
                "list_of_values": p.get_list_of_values(),
                "default": p.get_default_value(),
                "expected": p.get_expected_entries()
            }
            self.log.debug("Parameter results : {0}".format(result))
        return result

    def fill_parameters(self, data):
        """ Fill parameters with the provided data
        @param data: dictionnary with parameter name as key, and a dictionnary of {key: value} entries to fill the parameter
        @return True if the filling has been done
        @raise IndexError when provided name is not registered as a Parameter name
        @raise ValueError when parameter has not been correctly filled with provided values.
        Note that this exception has to be raised by the Parameter
        """
        params = {}
        for name, val in data.items():
            param = name.split('.')
#            print("  fill : ", name, val, param)
            if len(param) == 2:
                paramn = param[0]
                param = param[1]
                if paramn in self._parameters:
                    if paramn not in params:
                        params[paramn] = []
                    params[paramn].append({param: val})
#        print("   ***** ", params)
        for test, param in params.items():
            self._parameters[test].fill(param)

    def add_parameter(self, name, classname):
        """ Helper to add a parameter's instance to your Test instance
        @param name: the name you want to give to this parameter
        @param module : name of the module/class to load (as string). Should be something like "filename.ClassName",
        the "path" of domogik will be appended
        @raise ImportError if the module can't be imported
        @raise AttributeError if a parameter with this name already exists
        """
        if name in self._parameters:
            raise AttributeError("A parameter instance already exists with this name")
        modonly = classname.split('.')[0]
        classonly = classname.split('.')[1]
        module_name = "domogik.scenario.parameters.{0}".format(modonly)
        #This may raise ImportError
        cname = getattr(__import__(module_name, fromlist = [modonly]), classonly)
        p = cname(log=self.log, trigger=self.cb_trigger)
        self._parameters[name] = p

    def destroy(self):
        """ destroy all parameters
        """
        for p in self.get_raw_parameters():
            self.get_raw_parameters()[p].destroy()

    def evaluate(self):
        """ This is the main method of a test.
        This method MUST be implemented in the test class
        Basically, this method should :
          - call evaluate() method on each parameter
          - if all parameter returned a value, compute the test
        @return a boolean if the evaluation has been done, or None if the evaluation can't be done
        """
        raise NotImplementedError

    def get_blockly(self):
        return ""

    def on_message(self, did, msg):
        pass

