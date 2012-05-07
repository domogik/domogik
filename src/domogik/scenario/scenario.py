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

Base class for all scenarios

Implements
==========

- BasePlugin

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.common import TimeCond, StateCond

#The name of the class that should be loaded
CLASSNAME="Scenario"

class Scenario:
    """ This class should be extended by any Scenario. 
    It provides some convenient functions to manage a scenario 
    """

    def __init__(self, manager, log, uid):
        """ Create the instance
        @param : a scenarios manager instance
        @param log : a Logger instance
        @param uid : The instance's unique id
        This method should not be overloaded.
        Instance creation should only be done by the manager
        """
        self._mgr = manager
        self._log = log
        #Contains a list of (time|state) conditions identified by a unique ID
        self._cond = {}
        #Contains the list of item we want to listen to
        #This dictionnary will be populated by (time|state) methods during init phase
        #and will be fetch by the manager
        self._items = {}
        #Will be set by the manager when new data will arrive
        self._result_value = {}
        self._uid = uid

    def set_result_values(self, dict):
        """ Set an internal variable with the results
        @param dict : a dictionnary which contains all the results
        """
        self._result_value = dict 

    def condition(self, p, init):
        """ This method should create the condition.
        @param p : a dictionnary with the parameters' value provided by the user
        @param init : a boolean which is set to True when the condition is evaluated for the first time.
        The condition can be anything that can return a boolean value.
        Each part of the condition can be :
          - A method which returns a boolean
          - A call to the self.state_cond function
          - A call to the self.time_cond function
        The first time the metod will be called, the 'init' parameter will be set to True,
        so that each part of the condition knows that it's the initialization step.
        @warning The method called must NOT change anything when they are called outside the initialization step,
        because they will be called more than one time. Use self.result for this.
        @return True or False
        """
        raise NotImplementedError, "create_condition method MUST be overloaded"
    
    def result(self):
        """ This method is triggered by the manager when the condition is evaluated to True
        This method MUST be overloaded.
        It should contains anything that you want to be done when the condition is evaluated 
        to True (outside of init step of course)
        """
        raise NotImplementedError, "result method MUST be overloaded"

    def state_cond(self, init, technology, item_name, operator, value):
        """ Wrapper to create a StateCond item.
        @param manager : The scenarios manager instance
        @param technology : technolgy of the item (eg : x10, 1wire, etc ...)
        @param item_name : name of the item (eg: A1 for x10, 10B037A5010800DC
        for 1wire)
        @param operator : any comparison operator that python recognize
        When called with init == True, it will create a StateCond instance,
        call the "parse" method to know which listener it should create, and create them.
        Finally, it will put the StateCond instance in self._cond dictionnaries, identified 
        by a hash made like this : 
          hash("%s%s%s%s" % (technology, item_name, operator, value))
        In init mode, this method will return True, remember it is arbitrary and must not 
        be used for any eval 
        When called with init == False, this method will call the run() method of the instance
        fetched from self._cond
        """
        h = hash("%s%s%s%s" % (technology, item_name, operator, value))
        if init:
            if h in self._cond:
                #This will arrive if you use the same state_cond more than one time 
                # in a condition
                self._log.info("A cond already exists with hash : %s" % h)
                return True
            else:
                cond = StateCond(technology, item_name, operator, value)
                self._cond[h] = cond 
                items = cond.parse()
                return True
        else:
            if not h in self._cond:
                self._log.error("Hash %s not in conditions dictionnary !" % h)
                raise ValueError
            else:
                return self._cond[h].run(self._result_value)


    def time_cond(self, init, year, month, day, daynumber, hour, minute):
        """ Wrapper to create a TimeCond item.
        @param year
        @param month
        @param day
        @param daynumber : 0 - 6 for Monday - Sunday
        @param hour
        @param minute
        Refer to state_cond docstring to understand how it will work.
        """
        h = hash("%s%s%s%s%s%s" % (year, month, day, daynumber, hour, minute))
        if init:
            if h in self._cond:
                #This will arrive if you use the same state_cond more than one time 
                # in a condition
                self._log.info("A cond already exists with hash : %s" % h)
                return True
            else:
                cond = TimeCond(year, month, day, daynumber, hour, minute)
                self._cond[h] = cond 
                items = cond.parse()
                return True
        else:
            if not h in self._cond:
                self._log.error("Hash %s not in conditions dictionnary !" % h)
                raise ValueError
            else:
                return self._cond[h].run(self._result_value)
                
    def add_to_listener_list(self, technology, device):
        """ Add a technology + device item to the list that will be used to create 
        listeners. This method is called by time_cond and state_cond.
        @param technology : the technology name
        @param device : the device name

        """

