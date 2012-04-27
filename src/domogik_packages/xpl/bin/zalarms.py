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

Poor interface to plugincron

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.plugin import XplPlugin
import datetime
from domogik_packages.xpl.lib.zalarms import zalarmsAPI
import traceback
import logging

class zalarms(XplPlugin):
    '''
    Program alarms to the cron plugin    '''
    def __init__(self):
        """
        Create the zalarms class
        """
        XplPlugin.__init__(self, name = 'zalarms')
        self._config = Query(self.myxpl, self.log)

        try:
            self._myapi = zalarmsAPI(self._config,self.myxpl,self.log)
            #Listener(self.request_cmnd_cb, self.myxpl,
            #     {'schema': 'timer.request', 'xpltype': 'xpl-cmnd'})
            self.enable_hbeat()
        except:
            error = "Something went wrong during API init : %s" %  \
                     (traceback.format_exc())
            self.log.exception(error)

    def __del__(self):
        """
        Remove the zalarms class
        """
        del(self._myapy)
        XplPlugin.__del__(self)

    def request_cmnd_cb(self, message):
        """
        General callback for timer.request messages
        @param message : an XplMessage object
        """
        self._myapi.requestListener(message)


if __name__ == "__main__":
    zalarms()
