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
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.knx import KNXException
from domogik.xpl.lib.knx import KNX
import threading
import subprocess

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
        device = self._config.query('knx', 'device')

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
        Listener(self.knx_cmd, self.myxpl,{'schema':'knx.basic'})
        self.enable_hbeat()
        self.log.info("Plugin ready :)")


    def send_xpl(self, data):
        """ Send xpl-trig to give status change
        """
        sender=data[data.find('from')+4:data.find('to')-1]
        sender = sender.strip()
        if sender<>"pageination":
            #print "%s" %sender
           command = data[0:4]  
           msg_type="s"
           if data[-2:-1]==" ":
               msg_type="l" 
           if command <> 'Read':
               groups = data[data.find('to')+2:data.find(':')]
               groups = groups.strip()
#            print "%s" %groups
               groups = groups.replace('/',':')
#            print "%s" %groups
               val=data[data.find(':')+1:-1]
               val = val.strip()
               msg = XplMessage()
               msg.set_type("xpl-trig")
               msg.set_schema('knx.basic')
         #   if command == 'Writ':
         #       command = 'Write'
         #   if command == 'Resp':
         #       command = 'Responce'
            #msg.add_data({'type': command})
               msg.add_data({'group' :  groups})
               msg.add_data({'type' :  msg_type})
               msg.add_data({'response' :  val})
               self.myxpl.send(msg)
               
    def knx_cmd(self, message):
        print "%s" % message
        # type_cmd = message.data['type']
        groups = message.data['group']
        groups = groups.replace(':','/')
        valeur = message.data['data']
        data_type = message.data['type']
        #if type_cmd=="Write":
        if data_type=="s":
           command="groupswrite ip:127.0.0.1 %s %s" %(groups, valeur)
        if data_type=="l":
           command="groupwrite ip:127.0.0.1 %s %s" %(groups, valeur)
        #if type_cmd == "Read":
        #    command="groupsread ip:127.0.0.1 %s" % groups

        subp=subprocess.Popen(command, shell=True)



if __name__ == "__main__":
    INST = KNXManager()


