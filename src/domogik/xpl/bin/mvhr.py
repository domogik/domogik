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

Calculate efficiency of a MVHR

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.helperplugin import XplHlpPlugin
from domogik.xpl.lib.mvhr import HvacMvhr
import traceback
#import logging
#logging.basicConfig()

class Mvhr(XplHlpPlugin):
    '''
    Manage mvhr schema over XPL
    '''
    def __init__(self):
        """
        Create the mvhr class
        """
        XplHlpPlugin.__init__(self, name = 'mvhr')
        self.log.info("mvhr.__init__ : Start ...")
        self.config = Query(self.myxpl, self.log)

        self.log.debug("mvhr.__init__ : Try to start the mvhr library")
        try:
            self._mymvhr = HvacMvhr(self.config, self.log, self.myxpl)
        except:
            error = "Something went wrong during mvhrAPI init : %s" %  \
                (traceback.format_exc())
            self.log.exception("mvhr.__init__ : "+error)

        self.log.debug("mvhr.__init__ : Try to create listeners")
        Listener(self.mvhr_request_cmnd, self.myxpl,
                 {'schema': 'mvhr.request', 'xpltype': 'xpl-cmnd'})
        Listener(self.sensor_basic_trig, self.myxpl,
                 {'schema': 'sensor.basic', 'xpltype': 'xpl-trig'})
#        Listener(self.mvhr_basic_trig, self.myxpl,
#                 {'schema': 'mvhr.basic', 'xpltype': 'xpl-trig'})
#        Listener(self.mvhr_reload_config, self.myxpl,
#                 {'schema': 'domogik.system', 'xpltype': 'xpl-cmnd',
#                  'command': 'reload', 'plugin': 'mvhr'})
        self.helpers =   \
           { "status" :
              {
                "cb" : self._mymvhr.helper_status,
                "desc" : "Show status of the mvhr",
                "usage" : "status",
                "param-list" : "",
              },
              "reload_config" :
              {
                "cb" : self._mymvhr.helper_reload_config,
                "desc" : "Reload config of the plugin",
                "usage" : "reload_config",
                "param-list" : "",
              },
            }
        self.enable_helper()
        self.enable_hbeat()
        self._mymvhr.reload_config()
        self.log.info("mvhr plugin correctly started")

    #def __del__(self):
        #"""
        #Delete the mvhr plugin
        #"""
        #self._mymvhr.leave()
        #XplHlpPlugin.__del__(self)


    def mvhr_reload_config(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self._mymvhr.reload_config()

    def mvhr_request_cmnd(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self._mymvhr.request_listener(self.myxpl, message)

    def sensor_basic_trig(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self._mymvhr.sensor_trig_listener(self.myxpl, message)

    def mvhr_basic_trig(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self._mymvhr.mvhr_trig_listener(self.myxpl, message)

if __name__ == "__main__":
    Mvhr()
