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

Karotz management

Implements
==========

- KarotzMain

@author: Cedric BOLLINI <cb.dev@sfr.fr>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
"""

from domogik.xpl.common.xplconnector import Listener, XplTimer
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.karotz import Karotz
import traceback



class KarotzMain(XplPlugin):
    '''Manage ZiBase
    '''    
    def __init__(self):
        """ Create lister and launch bg listening
        """
        try:
            XplPlugin.__init__(self, name = 'karotz')
        except:
            self.log.error("Error to create Karotz Xplplugin=%s" % (traceback.format_exc()))
            return
            
        self._config = Query(self.myxpl, self.log)

        self.instid = self._config.query('karotz', 'installid')
        self.lang = self._config.query('karotz', 'language')
        
        try:
            self.log.info("Starting library")
            self.karotz=Karotz(self.log,self.instid)
            self.log.info("Started")
        except:
            self.log.error("Error to create Karotz object=%s" % (traceback.format_exc()))
            return

                
        self.log.info("Creating listener for Karotz")
        Listener(self.xpl_command, self.myxpl, {'schema': 'karotz.basic', 'xpltype': 'xpl-cmnd'})
        

        #self.add_stop_cb(self.stop)
        self.enable_hbeat()

        self.log.info("Plugin ready :)")
        
    def xpl_command(self, message):
        """ Call karotz lib function in function of given xpl message
            @param message : xpl message
        """
        cmd = None
        dev = None
        value = None
        
        if 'command' in message.data:
            cmd = message.data['command']
        if 'device' in message.data:
            device = message.data['device']
        if 'value' in message.data:
            value=message.data['value']
        if 'time' in message.data:
            tps=message.data['time']
        if 'right' in message.data:
            right=message.data['right']
            value=right
        if 'left' in message.data:
            left=message.data['left']

        self.log.debug(message.data)
        if value == None :
            self.log.warning("value not specified")
            return
        else:
            #self.log.debug("xpl %s received : device = %s value=%s " % (cmd, device, value))
            self.log.debug("xpl %s received " % (cmd) )    

            try:
                if cmd=='tts':
                    self.log.debug("xpl command=%s language=%s" % (cmd, self.lang))
                    self.karotz.tts(value,self.lang.upper())
                if cmd=='led':
                    self.log.debug("xpl command=%s color=%s time=%s" % (cmd, value,tps))
                    self.karotz.led(value,tps)
                if cmd=='ears':
                    self.log.debug("xpl command=%s right=%s left=%s" % (cmd, right, left))
                    self.karotz.ears(right,left)
            except:
                self.log.error("Error to send command=%s" % (traceback.format_exc()))
  

if __name__ == "__main__":
    KarotzMain()
