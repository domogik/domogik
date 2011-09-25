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

Get informations about one wire network

Implements
==========

TODO

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.onewire import OneWireException
from domogik.xpl.lib.onewire import OneWireNetwork
from domogik.xpl.lib.onewire import ComponentDs18b20
from domogik.xpl.lib.onewire import ComponentDs18s20
from domogik.xpl.lib.onewire import ComponentDs2401
from domogik.xpl.lib.onewire import ComponentDs2438
import ow
import traceback
import time
import threading


class OneWireManager(XplPlugin):

    def __init__(self):
        """ Init onewire 
        """
        XplPlugin.__init__(self, name='onewire')
        try:
            ### get all config keys
            self._config = Query(self.myxpl, self.log)
            device = self._config.query('onewire', 'device')

            cache = self._config.query('onewire', 'cache')
            if cache == "True":
                cache = True
            else:
                cache = False

            ### DS18B20 config
            ds18b20_enabled = self._config.query('onewire', 'ds18b20-en')

            ds18b20_interval = self._config.query('onewire', 'ds18b20-int')
    
            ds18b20_resolution = self._config.query('onewire', 'ds18b20-res')
    
            ### DS18S20 config
            ds18s20_enabled = self._config.query('onewire', 'ds18s20-en')

            ds18s20_interval = self._config.query('onewire', 'ds18s20-int')
    
            ### DS2401 config
            ds2401_enabled = self._config.query('onewire', 'ds2401-en')

            ds2401_interval = self._config.query('onewire', 'ds2401-int')
    
            ### DS2438 config
            ds2438_enabled = self._config.query('onewire', 'ds2438-en')

            ds2438_interval = self._config.query('onewire', 'ds2438-int')
    
            ### Open one wire network
            try:
                ow = OneWireNetwork(self.log, device, cache)
            except OneWireException as e:
                self.log.error(e.value)
                print(e.value)
                self.force_leave()
                return
            
    
            ### DS18B20 support
            if ds18b20_enabled == "True":
                self.log.info("DS18B20 support enabled")
                ds18b20 = threading.Thread(None, 
                                           ComponentDs18b20, 
                                           None,
                                           (self.log,
                                            ow, 
                                            float(ds18b20_interval), 
                                            ds18b20_resolution,
                                            self.send_xpl,
                                            self.get_stop()),
                                           {})
                ds18b20.start()
    
            ### DS18S20 support
            if ds18s20_enabled == "True":
                self.log.info("DS18S20 support enabled")
                ds18s20 = threading.Thread(None, 
                                           ComponentDs18s20, 
                                           None,
                                           (self.log,
                                            ow, 
                                            float(ds18s20_interval), 
                                            self.send_xpl,
                                            self.get_stop()),
                                           {})
                ds18s20.start()
    
            ### DS2401 support
            if ds2401_enabled == "True":
                self.log.info("DS2401 support enabled")
                ds2401 = threading.Thread(None, 
                                           ComponentDs2401, 
                                           None,
                                           (self.log,
                                            ow, 
                                            float(ds2401_interval), 
                                            self.send_xpl,
                                            self.get_stop()),
                                           {})
                ds2401.start()
    
            ### DS2438 support
            if ds2438_enabled == "True":
                self.log.info("DS2438 support enabled")
                ds2438 = threading.Thread(None, 
                                           ComponentDs2438, 
                                           None,
                                           (self.log,
                                            ow, 
                                            float(ds2438_interval), 
                                            self.send_xpl,
                                            self.get_stop()),
                                           {})
                ds2438.start()
    
        except:
            self.log.error("Plugin error : stopping plugin... Trace : %s" % traceback.format_exc())
            print(traceback.format_exc())
            self.force_leave()
        self.enable_hbeat()



    def send_xpl(self, type, data):
        """ Send data on xPL network
            @param data : data to send (dict)
        """
        msg = XplMessage()
        msg.set_type(type)
        msg.set_schema("sensor.basic")
        for element in data:
            msg.add_data({element : data[element]})
        self.log.debug("Send xpl message...")
        self.myxpl.send(msg)



if __name__ == "__main__":
    ow = OneWireManager()
