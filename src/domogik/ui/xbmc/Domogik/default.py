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

Auto load of xbmc domogik script

Implements
==========

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
#Check python version
if sys.version_info[0] < 2 or (sys.version_info[0] == 2 and sys.version_info[1] < 5):
    raise EnvironmentError, "You must use python 2.5 or more, please recompile \
            xbmc with --enable-external-python."

import os
import ConfigParser
config = ConfigParser.ConfigParser()
config.read("%s/.domogik/domogik.cfg" % os.getenv("HOME"))
python_path = config.get("python","path")
sys.path.extend(eval(python_path))
#add non-default include path
import main

#Update python path to avoid issue 1

w = DMGWindow()
w.doModal()

del w
