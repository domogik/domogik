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

Command Relay on Foscam camera

Implements
==========


@author: capof <capof1000 at gmail.com>
@copyright: (C) 2011 Domogik project
@license: GPL(v3)
@organization: Domogik

Library
"""

from domogik.xpl.common.xplconnector import XplTimer
from threading import Thread, Event
import subprocess
import time
import traceback
import urllib
import time

class command:

    def __init__(self, log):
        """
        Init object
        @param log : logger instance
        """
        self._log = log

    def clean(self, ip, port, user, password,device):
        """
        close the relay 
        """
        self._log.info("Start processing Close Command on %s  " % (device))
        
        try:
            self.url1 = "http://%s:%s/decoder_control.cgi?command=94&user=%s&pwd=%s" % (ip, port, user, password)
            #print self.url1 
            f = urllib.urlopen("http://192.168.1.32/decoder_control.cgi?command=94&user=admin&pwd=")
            self._log.debug("Trying to acces to Close URL  %s  " % (self.url1))
            if f.read().strip() == "ok.":
               self._log.debug("Close Command Url response %s  " % (f.read().strip()))
               return True
            else:
               self._log.error("Fail to closed Foscam relay : %s" % traceback.format_exc())
               return False
        except:
            self._log.error("Fail to close Foscam relay : %s" % traceback.format_exc())
            return False

