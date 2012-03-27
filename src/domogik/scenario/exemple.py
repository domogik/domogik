thon
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

from domogik.scenario.scenario import Scenario


CLASSNAME="MySample"
 
class MySample(Scenario):
 
    def condition(self, p, init):
         return self.state_cond(init, p["techno"], p["device"], p["oper"], p["value"])
 
    def result(self):
         some_function_to_send_email("me@me.com","Hey, it's %s %s !" % (p["oper"], p["value"]))

