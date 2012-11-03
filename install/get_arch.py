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

Little script to get correct architecture name

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import platform

def get_path(dir_only=False):
    arch = platform.machine()
    hub = {
        'x86_64' : 'src/domogik/xpl/tools/64bit/',
        'i686' : 'src/domogik/xpl/tools/32bit/',
        'arm' : 'src/domogik/xpl/tools/arm/',
        'armv5tel' : 'src/domogik/xpl/tools/arm/',
        'armv6l' : 'src/domogik/xpl/tools/arm/'
    }
    if arch not in hub.keys():
        return None
    else:
        if not dir_only:
            return hub[arch] + "xPL_Hub"
        else:
            return hub[arch] 

if __name__ == "__main__":
    print(get_path(True))
