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

class Ipx800(Helper)

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.xpl.lib.ipx800 import IPX
from domogik.xpl.lib.ipx800 import IPXException
from domogik.common import logger


class Ipx800(Helper):
    """ IPX800 helpers
    """

    def __init__(self):
        """ Init IPX 800 helper
        """

        self.commands =   \
               { "find" :
                  {
                    "cb" : self.find,
                    "desc" : "Find IPX 800 relay boards"
                  },
                 "status" :
                  {
                    "cb" : self.status,
                    "desc" : "Display all IPX800 elements status",
                    "min_args" : 1,
                    "usage" : "status <IPX 800 ip>"
                  }
                }

        log = logger.Logger('ipx800-helper')
        self._log = log.get_logger('ipx800-helper')
          


    def find(self, args = None):
        """ Try to find IPX800 relay boards
        """
        # Init IPX
        ipx  = IPX(self._log, None)
        
        # Find boards
        data = []
        data.append("List of all IPX800 boards found :")
        try:
            for ipx in ipx.find():
                data.append("%s : %s" % (ipx[0], ipx[1]))
        except IPXException as err:
            return [err.value]
        print data
        return data

    def status(self, args = None):
        """ Get status for relay, inputs, counter, etc
        """
            
        ipx = IPX(self._log, None)
        if len(args) == 1:
            ipx.open("foo", args[0])
        elif len(args) == 3:
            ipx.open("foo", args[0], args[1], args[2])
        else:
            return ["Bad usage of this helper"]
        data = ipx.get_status_for_helper()
        print data
        return data

MY_CLASS = {"cb" : Ipx800}



