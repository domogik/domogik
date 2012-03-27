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
@copyright: (C) 2007-2012 Domogik project
"""
from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.xpl.lib.telldus import telldusException
from domogik.xpl.lib.telldus import telldusAPI
from domogik.common import logger
from domogik.xpl.common.queryconfig import Query

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
                    "desc" : "List devices referenced by the telldus",
                    "min_args" : 1,
                    "usage" : "list all|devicetype"
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
       # self._config = Query(self.myxpl, self._log)
        self.tdapi  = telldusAPI(None,self._log,None,None)

    def list(self, args = None):
        """
        List all devices
        """
        self._log.info("telldusHelper.list : Start ...")
        data = []
        if  args[0]=="all":
            data.append("List all devices :")
            data.append("id : XPL id : Name")

            # List devices
            for key in self.tdapi.getDevices().iterkeys():
                add=self.tdapi.getDeviceAddress(key)
                name=self.tdapi.getDeviceName(key)
                data.append("%s  :  %s  : %s" % (str(key),add,name.encode("ascii", "ignore")))
        else:
            data.append("List all devices of type %s :" % args[0])
            data.append("id : XPL id : Name")
            self._log.debug("telldusHelper.list devicetype=%s" % args[0])

            # List devices
            for key in self.tdapi.getDevices().iterkeys():
                add=self.tdapi.getDeviceAddress(key)
                name=self.tdapi.getDeviceName(key)
                self._log.debug("telldusHelper.list for device= %s if devicetype==%s : '%s'" % (key,args[0],self.tdapi.isDevicetype(key,str(args[0]))))
                if self.tdapi.isDevicetype(key,str(args[0])):
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
        if len(args) == 1:
            data.extend(self.tdapi.getInfo(int(args[0])))
        else:
            return ["Bad usage of this helper. "]
        self._log.debug("telldusHelper.info : Done")
        return data

MY_CLASS = {"cb" : telldus}



