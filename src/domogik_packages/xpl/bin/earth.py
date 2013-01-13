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

Earth events server (dawn, dusk, zenith)

Implements
==========
Class Earth

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.earth import EarthAPI
from domogik_packages.xpl.lib.cron_query import CronQuery
import traceback

#import logging

class Earth(XplPlugin):
    '''
    The plugin itself.

    '''
    def __init__(self):
        """
        Create the cron class
        """
        XplPlugin.__init__(self, name = 'earth')
        self.log.debug("__init__ : Start ...")

        self.config = Query(self.myxpl, self.log)
        try:
            delay_cron = int(self.config.query('earth', 'delay-cron'))
        except:
            delay_cron = 30
            error = "Can't get configuration from XPL : %s" %  (traceback.format_exc())
            self.log.warning("__init__ : " + error)
            self.log.warning("Continue with default values.")

        cron = CronQuery(self.myxpl, self.log)
        cont = 3
        cron_started = False
        while not self.get_stop().isSet() and cont>=0:
            try :
                res = cron.is_running_server()
            except :
                pass
            if res :
                cron_started = True
                cont = -1
            else:
                self.log.debug("Can't talk to cron plugin. Retries=%s" % cont)
                self.get_stop().wait(delay_cron)
                cont -= 1
        if not cron_started :
            self.force_leave()
            error = "Can't talk to cron plugin. Exiting ..."
            self.log.error("__init__ : "+error)
            return
        else :
            self.log.info("Communication with the cron plugin established.")
        self.log.debug("__init__ : Try to start the earth API")
        try:
            self._earth = EarthAPI(self.log, self.config, self.myxpl, \
                            self.get_data_files_directory(), \
                            self.get_stop(), self.get_sanitized_hostname())
        except:
            self.force_leave()
            error = "Something went wrong during EarthAPI init : %s" %  \
                     (traceback.format_exc())
            self.log.error("__init__ : "+error)
            return

        self.log.debug("__init__ : Try to create listeners")
        Listener(self.request_cb, self.myxpl,
             {'schema': 'earth.request', 'xpltype': 'xpl-cmnd'})
        Listener(self.fired_cb, self.myxpl,
              {'schema': 'earth.basic', 'xpltype': 'xpl-trig', 'current': 'fired'})
        Listener(self.basic_cb, self.myxpl,
             {'schema': 'earth.basic', 'xpltype': 'xpl-cmnd'})

        self.add_stop_cb(self._earth.stop_all)

        self.log.debug("__init__ : Enable the heartbeat")
        self.enable_hbeat()

        self._earth.plugin_enabled(True)

        self.log.info("Plugin earth correctly started.")

    def request_cb(self, message):
        """
        General callback for timer.request messages

        @param message : an XplMessage object

        """
        self.log.debug("request_cb() : Start ...")
        self._earth.command_listener(self.myxpl, message)
        self.log.debug("request_cb() : Done :)")

    def basic_cb(self, message):
        """
        General callback for timer.basic messages

        @param message : an XplMessage object

        """
        self.log.debug("basic_cb() : Start ...")
        self._earth.action_listener(self.myxpl, message)
        self.log.debug("basic_cb() : Done :)")

    def fired_cb(self, message):
        """
        General callback for timer.basic messages

        @param message : an XplMessage object

        """
        self.log.debug("fired_cb() : Start ...")
        self._earth.fired_listener(self.myxpl, message)
        self.log.debug("fired_cb() : Done :)")

if __name__ == "__main__":
    Earth()
