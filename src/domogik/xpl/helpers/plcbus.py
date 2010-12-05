
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

Get informations about plcbus

@author: Capof <capof@wanadoo.fr> and Sp4rKy help
@copyright:(C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from threading import Event
import traceback
import time

from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.common import logger
from domogik.xpl.lib.plcbus import PLCBUSException
from domogik.xpl.lib.plcbus import PLCBUSAPI
from domogik.xpl.lib.PLCBusSerialHandler import serialHandler


ACCESS_ERROR = "Access to PLCBUS device is not possible. Does your user have the good permissions ? "

class plcbus(Helper):
    def __init__(self):
        self._event = Event()
        self.liste_found = []
        self.commands = \
            { "all" :
                {
                "cb" : self.all,
                "desc" : "Show all devices found on plcbus network",
                "min_args" : 2,
                "usage" : "find device for specified  house code <house code> and user code <user code>."
                },
              "detail" :
                {
                "cb" : self.detail,
                "desc" : "Show device detail ",
                "min_args" : 2,
                "usage" : "show status for specified device <device code> and user code <user code>"
                }
            }
        log = logger.Logger('plcbus-helper')
        self._log = log.get_logger()
        device = '/dev/plcbus'
        self.api1 = PLCBUSAPI(self._log, device, self._command_cb, self._message_cb)

    def detail(self, args = None):
        self._usercode = args[1]
        self._devicecode = args[0].upper()
        self.api1.send("STATUS_REQUEST", self._devicecode , self._usercode )
        #time.sleep(3)
        self._event.wait()
        self._event.clear()
        self.api1.stop()
        return self.liste_found


    def all(self, args = None):
        self._usercode = args[1]
        self._homecode = args[0].upper()
        self.api1.send("GET_ALL_ID_PULSE", self._homecode , self._usercode )
        time.sleep(1)
        self.api1.send("GET_ALL_ON_ID_PULSE", self._homecode , self._usercode )

        self._event.wait()
        self._event.clear()
        self.api1.stop()
        return self.liste_found

    def _command_cb(self, f):
        #print "DEBUG command : %s" % f["d_command"]
        #print "DEBUG data1 : %s" % f["d_data1"]
        #print "DEBUG data3 : %s" % f["d_data2"]
        if f["d_command"] == "GET_ALL_ID_PULSE":
            data = int("%s%s" % (f["d_data1"], f["d_data2"]))
            house = f["d_home_unit"][0]

            for i in range(0,16):
                unit = data >> i & 1
                code = "%s%s" % (house, i+1)
                if unit == 1 :
                    self.liste_found.append("%s" % (code))

        if f["d_command"] == "GET_ALL_ON_ID_PULSE":
            data = int("%s%s" % (f["d_data1"], f["d_data2"]))
            house = f["d_home_unit"][0]
            for i in range(0,16):
                unit = data >> i & 1
                code = "%s%s" % (house, i+1)
                if code in self.liste_found:
                    j = self.liste_found.index(code)
                    #self.liste_found.append("%s%s" % (j,"DEBUG index"))
                    if unit == 1:
                        #self.liste_found.append("%s%s" % (code,"DEBUG ONNNNNN"))
                        self.liste_found[j] = ("%s%s" % (self.liste_found[j]," ON"))
                    else:
                        #self.liste_found.append("%s%s" % (code,"DEBG OFFFFFF"))
                        self.liste_found[j] = ("%s%s" % (self.liste_found[j]," OFF"))
            self._event.set()

        
        if f["d_command"] == "STATUS_ON":
           print "command StatusRequest : %s" % f["d_command"]
           self.liste_found.append("%s%s%s%s%s" % (self._devicecode, " | Dimmer : ", f["d_data1"], " | Fading : ", f["d_data2"]))
           self._event.set()

    def _message_cb(self, message):
        print "Message : %s " % message

MY_CLASS = {"cb" : plcbus}
