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

class cidmodem(Helper)

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik_packages.xpl.lib.cidmodem import CallerIdModem 
from domogik_packages.xpl.lib.cidmodem import CallerIdModemException
from domogik.common import logger


class Cidmodem(Helper):
    """ cidmodem helpers
    """


    def __init__(self):
        """ Init Caller Id with a modem helper
        """

        self.commands =   \
               { "read" : 
                  {
                    "cb" : self.read,
                    "desc" : "Wait for a inbound call event",
                    "min_args" : 1,
                    "usage" : "read <device>"
                  },
                }

        log = logger.Logger('cidmodem-helper')
        self._log = log.get_logger('cidmodem-helper')
          


    def read(self, args = None):
        """ Read Modem until an inbound call
        """

        # Init Mir:ror
        cid  = CallerIdModem(self._log, None)
        
        # Open Modem
        try:
            cid.open(args[0])
        except CallerIdModemException as err:
            return [err.value]
            
        # read Modem
        while True:
            num = cid.read()
            if num != None:
                break

        # Close Modem
        try:
            cid.close()
        except CallerIdModemException as err:
            return [err.value]

        return ["Phone number : %s" % num]

MY_CLASS = {"cb" : Cidmodem}




