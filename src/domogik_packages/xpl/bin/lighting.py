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

xPL lighting manager

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.plugin import XplPlugin
from domogik_packages.xpl.lib.lighting import LightingAPI
from domogik_packages.xpl.lib.lighting import LightingException
import traceback
#import logging
#logging.basicConfig()

class Lighting(XplPlugin):
    '''
    Manage lighting schema over XPL
    '''
    def __init__(self):
        """
        Create the lighting class
        """
        XplPlugin.__init__(self, name = 'lighting')
        self.log.info("lighting.__init__ : Start ...")
        self._config = Query(self.myxpl, self.log)

        self.log.debug("lighting.__init__ : Try to get configuration from XPL")
        try:
            self.broadcast = bool(self._config.query('lighting', 'broadcast'))
        except:
            error = "Can't get configuration from XPL : %s" %  \
                     (traceback.format_exc())
            self.log.exception("lighting.__init__ : " + error)
            self.broadcast = True
            raise LightingException(error)

        self.log.debug("lighting.__init__ : Try to start the lighting librairy")
        try:
            self._mylighting = LightingAPI(self.broadcast, \
                self.myxpl, self.log, self.get_data_files_directory())
        except:
            error = "Something went wrong during lightingAPI init : %s" %  \
                     (traceback.format_exc())
            self.log.exception("lighting.__init__ : "+error)
            raise LightingException(error)

        self.log.debug("lighting.__init__ : Try to create listeners")
        Listener(self.lighting_config_cmnd, self.myxpl,
                 {'schema': 'lighting.config', 'xpltype': 'xpl-cmnd'})
        Listener(self.lighting_basic_cmnd, self.myxpl,
                 {'schema': 'lighting.basic', 'xpltype': 'xpl-cmnd'})
#        Listener(self.lighting_basic_trig, self.myxpl,
#                 {'schema': 'lighting.basic', 'xpltype': 'xpl-trig'})
        self.enable_hbeat()
        self.log.info("lighting plugin correctly started")

    def lighting_basic_trig(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self.log.debug("lighting_basic_trig() : Start ...")
        self._mylighting.basic_trig_listener(message)
        self.log.debug("lighting_basic_trig() : Done :)")

    def lighting_config_cmnd(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self.log.debug("lighting_config_cmnd() : Start ...")
        self._mylighting.config_cmnd_listener(message)
        self.log.debug("lighting_config_cmnd() : Done :)")

    def lighting_basic_cmnd(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self.log.debug("lighting_basic_cmnd() : Start ...")
        self._mylighting.basic_cmnd_listener(message)
        self.log.debug("lighting_basic_cmnd() : Done :)")

if __name__ == "__main__":
    Lighting()
