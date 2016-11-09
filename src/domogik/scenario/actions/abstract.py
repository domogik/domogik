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
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import traceback


class AbstractAction:
    """ This class provides base methods for the scenario actions.
    It must not be instanciated directly but need to be extended.
    An action is something called when a condition becomes True
    Many action can be part of the same scenario, launched by the same Condition.
    An action gets 4 parameters:
        - A logger
        - The condition that is linked to the Action's instance,
        - The array of tests used in the condition.
        - A Hash of extra parameters that can be used to customize action
    Thus, it is possible to query any test independently to generate action based
    on some tests' value.
    The main method of this class is do_action(), that need to be extended by each Action class.
    It takes no argument and should return some hash. See method documentation for more details
    The process is :
        - When Scenario is created, both the condition and the list of actions are defined.
          Each Action will be instanciated at this time. An UUID will be return to UI to map this
          Action's instance
        - For each action, user might have to fill some parameters.
          When the parameters are filled, the do_init() is called
        - When Condition is evaluated to 'True', each action linked to it is called (do_action())
    """

    def __init__(self, log=None, params=None):
        """ Create action's instance
        @param log : A logger instance
        @warn If you extend __init__, be sure that all parameters have a default value !
        """
        if log == None:
            # during MQ actions.list request, all classes are looked up and __init__ are called. But some__init__
            # need self._log.* functions, so we use logging as logger to avoid crashes.
            # indeed nothing will be logged in the log files, but this is not needed ass we just want the list of
            # actions and not launch them
            self._log = logging
        else:
            self._log = log
      
        self._description = ''
        self._params = {}

    def destroy(self):
        pass

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

    def do_init(self, params={}):
        """ This method is called when user provided the list of parameters (if needed)
        It can be used to initialize the action (using params).
        See get_expected_entries method to understand how you can provide to user the list of parameters.
        This method only store params in self._params by default.
        @param params : An extra Hash of parameters used by action, if we keep exemple inside `get_expected_entries`
        documentation, params could be {'mail': 'me@mybox.com'}
        """
        # we need to remove type and id => its not needed here
        # del params['type']
        # del params['id']
        self._params = params
        pass

    def set_param(self, param, val):
        self._params[param] = val

    def do_action(self, condition, tests):
        """ This is the most important method of this class. It does nothing by default and *must*
        be written by each Action class. This method should contain all the logic to trigger any action
        you want to be run.
        If you need to inialize things when the action is created, you can do it inside do_init().
        This method will always be called after do_init()
        2 parameters might be usefull :
            - condition : A Condition's instance, the one linked to the Action's instance and that was
            evaluated to "true".
            - tests = The list of tests' instance used in the condition. Can be usefull if you want to get the
            value of some part of the condition
        @param condition : a Condition's instance
        @param tests : the array of tests used by the condition
        """
        pass

    def get_expected_entries(self):
        """ Return a dictionnary of expected entries
        The expected entries are simply the name of the parameters the scenario manager (UI) should send with values
        filled by user, with some extra attributes : description and a type.
        Ex : { "mail": {
            "type" : "string",
            "description": "Address to send mail to",
            "default" : "default value or empty",
            "values" : [ "list","of","value","that","user","can","choose"],
            "filters" : [ "list","of","filters","or",""]
            }
        }
        The 'type' and 'description' are only informative, but the more precise you will be, the easier it will be for UI
        to send correct data without looking at your code to guess what you expect.
        @return a Hash of expected parameters, or {} if no parameters are needed
        """
        return {}
