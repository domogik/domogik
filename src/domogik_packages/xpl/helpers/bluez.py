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
Bluetooth detection.

Implements
==========
class BluezAPI

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from domogik.xpl.common.helper import Helper
#from domogik.xpl.common.helper import HelperError
from domogik.common import logger
from domogik.xpl.common.queryconfig import Query
import bluetooth
import traceback


class bluez(Helper):
    """
    bluez helpers
    """

    def __init__(self):
        """
        bluez helper
        """

        self.commands =   \
               { "scan" :
                  {
                    "cb" : self.scan,
                    "desc" : "Scan for bluetooth phones, ...",
                    "min_args" : 0,
                    "usage" : "scan"
                  },
                }

        log = logger.Logger('bluez-helper')
        self._log = log.get_logger('bluez-helper')

    def scan(self, args = None):
        """
        Scan for bluetooth devices
        """
        self._log.debug("scan : Start ...")
        data = []
        fmtret = "%-15s | %-15s"
        nb = 0
        try:
            nearby_devices = bluetooth.discover_devices()
            data.append(fmtret % ("Address", "Name"))
            data.append(fmtret % ("---------------", "---------------"))
            for bdaddr in nearby_devices:
                nb = nb+1
                target_name = bluetooth.lookup_name(bdaddr)
                data.append(fmtret % (bdaddr, target_name))                
            data.append(fmtret % ("---------------", "---------------"))
            data.append("Found %s bluetooth devices." % nb)
        except:
            data.append("Error with bluetooth adaptator. Look at logs.")
            self._log.error("Error with bluetooth adaptator")
            error = "traceback : %s" %  \
                 (traceback.format_exc())
            self._log.error("Exception : " + error)
        self._log.debug("telldusHelper.list : Done")
        return data

MY_CLASS = {"cb" : bluez}



