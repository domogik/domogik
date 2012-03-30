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

from exceptions import IndexError, NotImplementedError, AttributeError

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

    def __init__(self, log, xpl, trigger = None):
        """ Create the instance
        @param log : A logger instance
        @param xpl : The Xpl Manager instance
        @param trigger : a method to call when a parameter changes
        """
        self._log = log
        self._xpl = xpl
        self._trigger = trigger
        self._parameters = {}

    def cb_trigger(self, param):
        """ Callback called by a parameter when the fill() method is called
        Basically, it only calls the underlying ttrigger if exists
        """
        self._log.warning("Trigger %s called by parameter %s" % (self._trigger, param))
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
        result = {}
        for name in self._parameters:
            p = self._parameters[name]
            result[name] = {
                "type": p.get_type(),
                "filter": p.get_filters(),
                "list_of_values": p.get_list_of_values(),
                "default": p.get_default_value(),
                "expected": p.get_expected_entries()
            }
        return result

    def fill_parameters(self, data):
        """ Fill parameters with the provided data
        @param data: dictionnary with parameter name as key, and a dictionnary of {key: value} entries to fill the parameter
        @return True if the filling has been done
        @raise IndexError when provided name is not registered as a Parameter name
        @raise ValueError when parameter has not been correctly filled with provided values. 
        Note that this exception has to be raised by the Parameter
        """
        for name in data:
            if name not in self._parameters:
                raise IndexError("Name " + name + "is not in known parameters for this test")
            else:
                self._parameters[name].fill(data[name])

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
        module_name = "domogik.xpl.lib.rest.scenario.parameters.%s" % modonly
        #This may raise ImportError
        cname = getattr(__import__(module_name, fromlist = [modonly]), classonly)
        p = cname(self._log, self._xpl, self.cb_trigger)
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

