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

KNX bus

Implements
==========

- KnxManager

@author: Fritz <fritz.smh@gmail.com> Basilic <Basilic3@hotmail.com>...
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin, XplResult
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.knx import KNXException
from domogik.xpl.lib.knx import KNX
import threading


class KNXManager(XplPlugin):
    """ Implements a listener for KNX command messages 
        and launch background listening for KNX events
    """

    def __init__(self):
        """ Create listener and launch bg listening
        """
        XplPlugin.__init__(self, name = 'knx')

        # Configuration : KNX device
        self._config = Query(self.myxpl, self.log)
        res = XplResult()
        self._config.query('knx', 'device', res)
        device = res.get_value()['device']

        ### Create KNX object
        try:
            self.knx = KNX(self.log, self.send_xpl)
            self.log.info("Open KNX for device : %s" % device)
            self.knx.open(device)
        except KNXException as err:
            self.log.error(err.value)
            print err.value
            self.force_leave()
            return

        ### Start listening 
        try:
            self.log.info("Start listening to KNX")
            knx_listen = threading.Thread(None,
                                          self.knx.listen,
                                          None,
                                          (),
                                          {})
            knx_listen.start()
        except KNXException as err:
            self.log.error(err.value)
            print err.value
            self.force_leave()
            return

        ### Create listeners for commands
        self.log.info("Creating listener for KNX")
        # TODO

        self.enable_hbeat()
        self.log.info("Plugin ready :)")


    def send_xpl(self, data):
        """ Send xpl-trig to give status change
        """
	command = data[0:4]
        #print "command= %s" % command
        if command <> 'Read':
            groups = data[-10:-5]
	    val=data[-3:-1]
            #print "Data = %s " % data       
            #print "Groupe = %s " % groups 
            #print "Valeur = %s " % val
            msg = XplMessage()
            msg.set_type("xpl-trig")
            msg.set_schema('knx.basic')
            msg.add_data({'groups' :  groups})
        #msg.add_data({'type' :  msg_type})
            msg.add_data({'current' :  val})
            self.myxpl.send(msg)





if __name__ == "__main__":
    INST = KNXManager()


