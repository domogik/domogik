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

Get informations about IPX800

Implements
==========

class teleinfo(Helper)

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.xpl.lib.teleinfo import Teleinfo
from domogik.xpl.lib.teleinfo import TeleinfoException
from domogik.common import logger


class TeleinfoHelper(Helper):
    """ Teleinfo helpers
    """

    def __init__(self):
        """ Init Teleinfo helper
        """

        self.commands =   \
               { "read" :
                  {
                    "cb" : self.read,
                    "desc" : "Display electric meter informations",
                    "min_args" : 1,
                    "usage" : "read <device path>"
                  }
                }

        log = logger.Logger('teleinfo-helper')
        self._log = log.get_logger()
          

    def read(self, args = None):
        """ Read electrric meter
        """
            
        tele = Teleinfo(self._log, None)
        try:
            tele.open(args[0])
        except TeleinfoException as err:
            return [err.value]

        data = tele.read()

        try:
            tele.close()
        except TeleinfoException as err:
            return [err.value]

        resp = []
        resp.append("Electric meter data : ")
        for entry in data:
            resp.append("%-10s : %-15s" % (entry["name"], entry["value"]))
        return resp

MY_CLASS = {"cb" : TeleinfoHelper}



