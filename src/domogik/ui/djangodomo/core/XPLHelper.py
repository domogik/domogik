#!/usr/bin/python
#-*- encoding:utf-8 *-*

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author : Marc Schneider <marc@domogik.org>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2009-02-08 18:10:37 +0100 (dim. 08 févr. 2009) $
# $LastChangedRevision: 348 $

import os
from subprocess import *


class XPLHelper:
    """
    Utility class for xPL
    """

    def send(self, xPLSchema, xPLCommand):
        scriptCmd = "python sendXPL.py " + xPLSchema + " \"" + xPLCommand + "\""
        print scriptCmd
        curPath = os.getcwd()
        print curPath
        # TODO : chdir is fishy, please change me!
        # This will be changed when the new xPL API will be available
        os.chdir("../../xpl/bin")
        res = Popen(scriptCmd, shell=True, stderr=PIPE)
        os.chdir(curPath)
        output = res.stderr.read()
        print "output = %s" % output
        res.stderr.close()
        return output
