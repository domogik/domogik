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

Manage connection to the database

Implements
==========

- DBConnector.__init__(self)
- DBConnector._request_config_cb(self, message)
- DBConnector._send_config(self, technology, hostname, key, value, plugin, element = None)
- DBConnector._fetch_elmt_config(self, techno, element, key)
- DBConnector._fetch_techno_config(self, hostname, techno, key)
- DBConnector._update_stat(self, message)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import xPLPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.database import DbHelper

class DBConnector(xPLPlugin):
    '''
    Manage the connection between database and the xPL stuff
    Should be the *only* object with StatsManager to access the database in the core side
    '''

    def __init__(self):
        '''
        Initialize database and xPL connection
        '''
        xPLPlugin.__init__(self, 'dbmgr')
        self._log = self.get_my_logger()
        self._log.debug("Init database_manager instance")
        
        self._db = DbHelper()
        Listener(self._request_config_cb, self._myxpl,
                {'schema': 'domogik.config', 'xpltype': 'xpl-cmnd'})

    def _request_config_cb(self, message):
        '''
        Callback to receive a request for some config stuff
        @param message : the xPL message
        '''
        #try:
        techno = message.data['technology']
        hostname = message.data['hostname']
        key = message.data['key']
        if "element" in message.data:
            element = message.data['element']
        else:
            element = None
        if not key:
            self._log.debug("New request config received for %s :\
                    asked for all config items" % (techno))
        else:
            self._log.debug("New request config received for %s : %s" % (techno,
            key))
        if element:
            self._send_config(techno, hostname, key, self._fetch_elmt_config(techno,
            element, key), element)
        else:
            if not key:
                keys = self._fetch_techno_config(techno, hostname, key).keys()
                values = self._fetch_techno_config(techno, hostname, key).values()
                self._send_config(techno, hostname, keys, values)
                
            else:
                self._send_config(techno, hostname, key, self._fetch_techno_config(techno, hostname,
                key))
        #except KeyError:
         #   self._log.warning("A request for configuration has been received, but it was misformatted")

    def _send_config(self, technology, hostname, key, value, element = None):
        '''
        Send a config value message for an element's config item
        @param technology : the technology of the element
        @param hostname : hostname
        @param element :  the name of the element
        @param key : the key or list of keys of the config tuple(s) to fetch
        @param value : the value or list of values corresponding to the key(s)
        '''
        self._log.debug("Send config response for %s on %s : %s = %s" % (technology, hostname, key, value))
        mess = XplMessage()
        mess.set_type('xpl-stat')
        mess.set_schema('domogik.config')
        mess.add_data({'technology' :  technology})
        mess.add_data({'hostname' :  hostname})
        if element:
            mess.add_data({'element' :  element})
        #If key/value are lists, then we add a key=value for each item
        if isinstance(key, list):
            for (_key, _val) in zip(key, value):
                mess.add_data({_key :  _val})
        else:
            mess.add_data({key :  value})
#        mess.set_conf_key('target', plugin)
        self._myxpl.send(mess)

    def _fetch_elmt_config(self, techno, element, key):
        '''
        Fetch an element's config value in the database
        @param techno : the technology of the element
        @param element :  the name of the element
        @param key : the key of the config tuple to fetch
        '''
        #TODO : use the database
        vals = {'x10': {'a3': {},
                        'a2': {},
                        }

                }
        return vals[techno][element][key]

    def _fetch_techno_config(self, techno, hostname, key):
        '''
        Fetch a technology global config value in the database
        @param techno : the technology of the element
        @param hostname : hostname
        @param key : the key of the config tuple to fetch
        '''
        #Get technology id 

        #This array is here for information only but is not used anymore
        #Values are now on the database
        vals = {'x10': {'heyu-cfg-path':'/etc/heyu/x10.conf',
            'heyu-file-0': 'TTY /dev/ttyUSB0',
            'heyu-file-1': 'TTY_AUX /dev/ttyUSB0 RFXCOM',
            'heyu-file-2': 'ALIAS back_door D5 DS10A 0x677'},
                'global': {'pid-dir-path': '/tmp/'},
                'onewire': {'temperature_refresh_delay' : '10'},
                'cidmodem': {'device' : '/dev/ttyUSB1',
                           'nbmaxtry' : '10',
                           'interval' : '15'},
                'mirror': {'device' : '/dev/hidraw0',
                           'nbmaxtry' : '10',
                           'interval' : '15'},
                'xbmc_not': {'address' : '192.168.0.20:8080', 
                         'delay' : '15',
                         'maxdelay' : '20'},
                'gagenda': {'email' : "fritz.smh@gmail.com",
                         'password' : 'XXXXXXXX',
                         'calendarname' : 'fritz.smh@gmail.com',
                         'startup-plugin':'True'},
                'teleinfo' : {'device' : '/dev/teleinfo',
                    'interval' : '30'},
                    'dawndusk' : {'startup-plugin':'True'},
                    'plcbus' : {'device':'/dev/ttyUSB0'},
                }
        try:
            if key:
                val = self._db.get_plugin_config(techno, hostname, key).value
                return val
            else:
                vals = self._db.list_plugin_config(techno, hostname)
                res = {}
                for val in vals:
                    res[val.key] = val.value
                return res
        except:
            traceback.print_exc()
            self._log.warn("No config found for technolgy %s on %s, key %s" % (techno, hostname, key))
            return None

if __name__ == "__main__":
    DBC = DBConnector()
