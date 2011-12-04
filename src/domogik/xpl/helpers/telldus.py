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
xPL client through the TellStick and Tellstick Duo

Support Chacon/DIO, Nexa, Proove, Intertechno, HomeEasy, KlikAanKlikUit,
Byebye Standby, Rusta ... and many others 
For a list of supported protocols/models, please see the telldus-core 
documentation here : http://developer.telldus.se/wiki/TellStick_conf

Implements
==========

class telldusTool(Helper)

@author: Sebastien GALLET <sgallet@gmail.com>
@license: GPL(v3)
@copyright: (C) 2007-2009 Domogik project
"""
from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.xpl.lib.telldus import telldusException
from domogik.xpl.lib.telldus import telldusAPI
from domogik.common import logger


class telldus(Helper):
    """ 
    telldusTool helpers
    """

    def __init__(self):
        """ 
        telldusTool helper
        """

        self.commands =   \
               { "list" :
                  {
                    "cb" : self.list,
                    "desc" : "List all devices referenced by the telldus"
                  },
                 "info" :
                  {
                    "cb" : self.info,
                    "desc" : "Display device information",
                    "min_args" : 1,
                    "usage" : "info <id>"
                  }
                }

        log = logger.Logger('telldus-helper')
        self._log = log.get_logger('telldus-helper')

    def list(self, args = None):
        """ 
        List all devices
        """
        self._log.info("telldusHelper.list : Start ...")                
        data = []
        data.append("List of all devices :")
        data.append("id : XPL id : Name")

        tdapi  = telldusAPI(None,self._log,None)

        # List devices
        for key in tdapi._devices._data.iterkeys():
            add=tdapi.getDeviceAddress(key)
            name=tdapi.getDeviceName(key)
            data.append("%s  :  %s  : %s" % (str(key),add,name.encode("ascii", "ignore")))
        self._log.debug("telldusHelper.list : Done")                
        return data

    def info(self, args = None):
        """ 
        Get information for device
        """
        self._log.info("telldusHelper.info : Start ...")                            
        data = []
        data.append("Information for device %s" % args[0])
        tdapi  = telldusAPI(None,self._log,None)
        if len(args) == 1:
            data.extend(tdapi.getInfo(int(args[0])))
        else:
            return ["Bad usage of this helper. "]
        self._log.debug("telldusHelper.info : Done")                
        return data

MY_CLASS = {"cb" : telldus}



