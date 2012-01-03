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
import glob 

class ScenariosManager:
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

    def __init__(self, log):
        """ Create ScenarioManager instance
            @param log : Logger instance
        """

    def list_tests(self):
        """ Return the list of tests
        """

