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

Module purpose
==============

Send time informations on the network

Implements
==========

- xPLDateTime.__init__(self)
- xPLDateTime._f(self, nb)
- xPLDateTime._send_datetime(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.lib.module import xPLModule


class ModuleSample(xPLModule):
    '''
    Send date and time on the xPL network every minute
    '''

    def __init__(self):
        xPLModule.__init__(self, name = 'mdspl')

if __name__ == "__main__":
    ModuleSample()
