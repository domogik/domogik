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

Get informations about mirror and ztamps

Implements
==========

class Mirror(Helper)

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.xpl.lib.mirror import Mirror
from domogik.xpl.lib.mirror import MirrorException
from domogik.common import logger


class MirrorHelper(Helper):
    """ Mir:ror helpers
    """

    def __init__(self):
        """ Init Mir:ror helper
        """

        self.commands =   \
               { "read" : 
                  {
                    "cb" : self.read,
                    "desc" : "Wait for a Mir:ror event",
                    "min_args" : 1,
                    "usage" : "read <device>"
                  }
                }

        log = logger.Logger('mirror-helper')
        self._log = log.get_logger()
          

    def read(self, args = None):
        """ Read Mir:ror device until an event occurs
        """

        # Init Mir:ror
        mirror  = Mirror(self._log, None)
        
        # Open Mir:ror
        try:
            mirror.open(args[0])
        except MirrorException as err:
            return [err.value]
            
        # read Mir:ror
        while True:
            device, my_type, current = mirror.read()
            if device != None:
                return ["Device : %s" % device,
                        "Type : %s" % my_type,
                        "Current : %s" % current]

        # Close Mir:ror
        try:
            mirror.close()
        except MirrorException as err:
            return [err.value]


MY_CLASS = {"cb" : MirrorHelper}




