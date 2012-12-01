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

Dawndusk functionnalities

Implements
==========
Class bluetooth

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.dawndusk import BluezAPI
#from domogik_packages.xpl.lib.dawndusk import BluezException
from domogik.xpl.common.plugin import XplPlugin
#from domogik_packages.xpl.lib.helperplugin import XplHlpPlugin
import traceback
#import logging

class Dawndusk(XplPlugin):
    '''
    Manage
    '''
    def __init__(self):
        """
        Create the dawndusk plugin.
        """
        XplPlugin.__init__(self, name = 'dawndusk')
        self.log.info("__init__ : Start ...")
        self.config = Query(self.myxpl, self.log)

        self.log.debug("__init__ : Try to start the dawndusk API")
        try:
            self._dawndusk = BluezAPI(self.log, self.config, self.myxpl, \
                self.get_stop())
        except:
            error = "Something went wrong during dawnduskAPI init : %s" %  \
                     (traceback.format_exc())
            self.log.error("__init__ : "+error)

        self.log.debug("__init__ : Try to create listeners")
        Listener(self.basic_cmnd_cb, self.myxpl,
                 {'schema': 'dawndusk.basic', 'xpltype': 'xpl-cmnd'})

        #self.enable_helper()
        self.enable_hbeat()
        self._dawndusk.start_adaptator()
        self.log.info("Plugin dawndusk correctly started.")

    def basic_cmnd_cb(self, message):
        """
        General callback for dawndusk.basic messages
        @param message : an XplMessage object
        """
        self.log.debug("basic_cmnd_cb() : Start ...")
        self._dawndusk.basic_listener(message)
        self.log.debug("basic_cmnd_cb() : Done :)")

if __name__ == "__main__":
    Dawndusk()
