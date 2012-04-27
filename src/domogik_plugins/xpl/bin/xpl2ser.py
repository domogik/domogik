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

Xpl bridge between ethernet and serial 

Implements
==========

TODO


@author: Kriss
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from domogik.common.dmg_exceptions import XplMessageError
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik_plugins.xpl.lib.xpl2ser import XplBridge
from domogik_plugins.xpl.lib.xpl2ser import XplBridgeException
import threading
import traceback


class XplBridgeManager(XplPlugin):
    """ Send xpl message from hub to serial device
                    and vice versa
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='xpl2ser')

        # Configuration
        self._config = Query(self.myxpl, self.log)

        # Configuration : list of devices to check
        self.dev_list = {}
        num = 1
        loop = True
        while loop == True:
            dev = self._config.query('xpl2ser', 'device-%s' % str(num))
            if dev != None:
                self.log.info("Configuration : device=%s" % dev)
                # init object 
                baudrate = self._config.query('xpl2ser', 'baudrate-%s' % str(num))
                self.dev_list[dev] = { "baudrate" : baudrate }
                num += 1
            else:
                loop = False

        # no device configured
        if num == 1:
            msg = "No device configured. Exiting plugin"
            self.log.info(msg)
            print(msg)
            self.force_leave()
            return

        ### Start listening each device
        for dev in self.dev_list:
            try:
                self.dev_list[dev]["obj"] = XplBridge(self.log, self.send_xpl, self.get_stop())
                # Open serial device
                self.log.info("Open '%s'" % dev)
                try:
                    self.dev_list[dev]["obj"].open(dev, 
                                              self.dev_list[dev]["baudrate"])
                except XplBridgeException as e:
                    self.log.error(e.value)
                    print(e.value)
                    self.force_leave()
                    return
                self.log.info("Start listening for '%s'" % dev)
                dev_listen = threading.Thread(None,
                                              self.dev_list[dev]["obj"].listen,
                                              "listen_serial",
                                              (),
                                              {})
                dev_listen.start()
            except:
                self.log.error(traceback.format_exc())
                print(traceback.format_exc())
                # We don't quit plugin if an error occured
                # a device may have disappeared
                # Notice that it won't be read if device come back
                #self.force_leave()
                #return

        # Create listeners
        # Notice : this listener and callback function make this plugin send
        # on serial port each xpl message it reads on serial port
        # TODO : update this !
        #Listener(self.xplbridge_cb, self.myxpl)
 
        self.enable_hbeat()
        self.log.info("Plugin ready :)")

    def send_xpl(self, resp):
        """ Send xPL message on network
            @param resp : xpl message
        """
        print("Input xpl message : %s " % resp)
        try:
            msg = XplMessage(resp)
            self.myxpl.send(msg)
        except XplMessageError:
            error = "Bad data : %s" % traceback.format_exc()
            print(error)
            self.log.error(error)

    def xplbridge_cb(self, message):
        """ Call xplbridge lib for sending xpl message to serial
            @param message : xpl message to send
        """
        self.log.debug("Call xplbridge_cb")
        mesg = message.to_packet()
        # Write on serial device
        self.log.debug("Call write() ")
        self.br.write(mesg)

if __name__ == "__main__":
    XplBridgeManager()

