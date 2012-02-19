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

from exceptions import ValueError, NotImplementedError
from threading import Thread

class AbstractParameter:
    """ This class provides base method for the tests' parameters
    It must not be instanciated directly but need to be extended by parameters
    A parameter contains some "tokens" that can be filled by the user and evaluated later.
    Each parameter contains some access method, as well as an "evaluate" method, which MUST be extended by 
    child classes.
    """

    def __init__(self, log, xpl, trigger = None):
        """ Create the parameter instance
        The default init will only create the instance, and provide access to logging system and 
        xpl on self._log and self._xpl
        This method should be extended to set type, filter, etc ...
        @param log : a Logger instance
        @param xpl : A Xpl Manager instance
        @param trigger : a method to call when the status of the parameter is updated
        """
        self._log = log
        self._xpl = xpl
        self._type = None
        self._filters = {}
        self._list_of_values = {}
        self._default = {}
        self._expected = {}
        self._params = {}
        self._trigger = trigger
        self._thread = None

    def get_trigger(self):
        """ Return the trigger or None if no trigger was defined
        A trigger can be passed to notify underlying objects when one parameter is updated
        """
        return self._trigger

    def call_trigger(self):
        """ Call the trigger in a thread.
        Does nothing if no trigger is defined
        """
        print "calling trigger"
        if self._trigger == None:
            return
        else:
            self._thread = Thread(target=self._trigger,name = "call trigger %s" % self._trigger, args=[self])
            self._thread.start()

    def get_type(self):
        """ Return the current type
        @return a string with the "type" of the parameter or None if type is not set
        """
        return self._type

    def get_filters(self):
        """ Return a dictionnary of filters
        @return a dictionnary with "item" to filter as key, and a list of values to restrict to as value
        """
        return self._filters

    def get_list_of_values(self):
        """ Return the list of correct values for all entries
        If not empty, the user should only be able to choose one of those values for corresponding entry
        @return a list of correct values, or {} if no possible value is defined.
        """
        return self._list_of_values

    def get_default_value(self, entry = None):
        """ Return the default value for the entry if defined, else for all entries
        @return a string containing the default value, or None if no value is set
        """
        if entry == None:
            return self._default
        if entry not in self._default:
            return None
        else:
            return self._default[entry]

    def get_expected_entries(self):
        """ Return a dictionnary of expected entries
        The expected entries are simply the name of the parameters the scenario manager (UI) should send with values 
        filled by user, with some extra parameters : description and a type.
        Ex : { "time": {
            "type" : "timestamp",
            "description": "Expected time as timestamp"
            }
        }
        The 'type' and 'description' are only informative, but the more precise you will be, the easier it will be for UI 
        to send correct data without looking at your code to guess what you expect.
        Most of the time, only one value will be enough (time, operator, etc ...), but with more complex parameters, 
        maybe you'll need more (for a device state for ex, you may need the technology, the device address, maybe some 
        usercode, etc ...
        @return a list of expected parameters, or 
        """
        return self._expected

    def get_parameters(self):
        """ Return the parameters
        @return the internal parameters if they have been provided by user, {} elsewhere
        """
        return self._params 

    def set_type(self, tname = None):
        """ Set the type.
        @param tname : name of the parameter's type.
        The type is only a one-word to describe your parameter, it will help the UIs to better describes what you wait 
        to the users (the "form" for a device or a timestamp won't be the same)
        @raise ValueError if @tname is not a one-word string
        """
        if ( tname == None ) or ( type(tname) != str ) or ( len(tname.split(' ')) != 1 ):
            raise ValueError("`tname` must be a one-word string.")
        self._type = tname

    def add_filter(self, key, values):
        """ Add a filter to the restriction list. This filter will help UIs to restrict the choices offered to the user.
        The method will add the filter entry to the list, or update the existing value if one exists with the same key
        @param key : a word to describe what should be restricted, ex : housecode, usercode, address, month, etc ...
        @param values : a list of value to filter to, those values describe what should be *included*
        @raise ValueError if key is not a one-word string or if values is not a list
        """
        if ( key == None ) or ( type(key) != str ) or ( len(key.split(' ')) != 1 ):
            raise ValueError("`key` must be a one-word string.")
        if ( type(values) != list ):
            raise ValueError("`values` must be a list.")
        self._filters[key] = values

    def set_list_of_values(self, ename, lof):
        """ Set the list of authorized values for an entry
        @param ename : name of the entry, must be added by @add_expected_entry@ before
        @param lof : a list of string items that user can choose.
        @raise ValueError if lof is not a list of strings
        """
        if ename not in self._expected:
            raise ValueError("You must add the entry with @add_expected_entry@ before setting a list of values for it")
        if ( type(lof) != list ) or ( [i for i in lof if type(i) != str] != [] ):
            raise ValueError("`lof` must be a list of strings or an empty list.")
        self._list_of_values[ename] = lof

    def add_value_to_list(self, ename, value):
        """ Add a value to the list of authorized values for an entry
        @param ename : name of the entry, must be added by @add_expected_entry@ before
        @param value : a string to add
        @raise ValueError if value is not a string or ename is not defined
        Does nothing if the value already in list
        """
        if ename not in self._expected:
            raise ValueError("You must add the entry with @add_expected_entry@ before setting a list of values for it")
        if ( type(value) != str ):
            raise ValueError("`value` must be a string")
        if value in self._list_of_values[ename]:
            return
        self._list_of_values[ename].append(value)

    def set_default_value(self, ename, value):
        """ Set a default value for en entry
        This value should be preselected by the form
        @param ename : name of the entry, must be added by @add_expected_entry@ before
        @param value : a string to use as default value
        @raise ValueError if value is not a string
        """
        if ename not in self._expected:
            raise ValueError("You must add the entry with @add_expected_entry@ before setting a list of values for it")
        if ( type(value) != str ):
            raise ValueError("`value` must be a string")
        self._default[ename] = value

    def add_expected_entry(self, ename, etype, edesc):
        """ Add an entry to the list of expected entries, replace it if ename already present
        See @get_expected_entries@ for more description about expected entries
        @param ename : the name of the entry
        @param etype : the type of the entry in one word , ex : timestamp, int, string, date, etc ...
        @param edesc : a short description of the entry
        See @get_expected_entries@ for more details
        @raise ValueError if ename or etype are not  one-word strings
        """
        if ( type(ename) != str ) or ( type(etype) != str ) or ( ename == "" ) or ( etype == "" ) or ( edesc == "" ):
            raise ValueError("`ename` and `etype`_must be strings and no parameter can contain empty string")
        self._expected[ename] = { 
            "type" : etype, 
            "description" : edesc
        }

    def fill(self, params):
        """ Fill the internal parameters dictionnary with provided params
        @raise AttributeError if one entry provided in params is not defined
        @raise ValueError if a list_of_values has been defined for an entry and the submitted value is not in this list
        """
        for entry in params:
            if entry not in self._expected:
                raise AttributeError("Entry " + entry + "is not in list")
            if entry in self.get_list_of_values() and params[entry] not in self.get_list_of_values()[entry]:
                raise ValueError("The submitted value for entry " + entry + " is not in list of authorized values")
        self._params = params
        self.call_trigger()

    def evaluate(self):
        """ This method is called by the Test to evaluate the parameter.
        This method must return None if the value of the parameter can't be determined yet, or the value if it can
        Most of the time, the value can be determined as soon as the @fill@ method has been called. But sometimes not,
        for ex. the state of the device may need to wait for an xPL message. In that case None mus tbe returned until 
        the state is knonw.
        This method MUST be implemented in parameters child classes
        @return None if the value can't be determined, the value elsewhere
        @raise NotImplementedError if the child class dos not implement it
        """
        raise NotImplementedError

    def destroy(self):
        """ Destroy parameter
        This method is called by Test and can be extended to add some checks to destroy / stop part of the parameter
        """
        pass
