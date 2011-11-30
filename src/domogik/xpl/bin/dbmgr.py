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
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.database import DbHelper

class DBConnector(XplPlugin):
    '''
    Manage the connection between database and the xPL stuff
    Should be the *only* object along with the StatsManager to access to the database on the core side
    '''

    def __init__(self):
        '''
        Initialize database and xPL connection
        '''
        XplPlugin.__init__(self, 'dbmgr')
        self.log.debug("Init database_manager instance")
        try:
            self._db = DbHelper()
            self._engine = self._db.get_engine()
        except:
            self.log.error("Error while starting database engine : %s" % traceback.format_exc())
            self.force_leave()
            return

        Listener(self._request_config_cb, self.myxpl, {'schema': 'domogik.config', 'xpltype': 'xpl-cmnd'})
        self.enable_hbeat()

    def _request_config_cb(self, message):
        '''
        Callback to receive a request for some config stuff
        @param message : the xPL message
        '''
        print("request")
        #try:
        self._db = DbHelper(engine=self._engine)
        techno = message.data['technology']
        hostname = message.data['hostname']
        key = message.data['key']
        if "value" in message.data:
            new_value = message.data['value']
        else:
            new_value = None
        if "element" in message.data:
            element = message.data['element']
        else:
            element = None

        # Set configuration
        if new_value:
            self.log.debug("New set config received for %s : %s : %s" % (techno, key, new_value))
            self._set_config(techno, hostname, key, new_value)

        # Send configuration
        else:
            if element:
                self.log.debug("New request config received for %s : %s : %s" % (techno, key, element))
                self._send_config(techno, hostname, key, self._fetch_elmt_config(techno, element, key), element)
            else:
                if not key:
                    self.log.debug("New request config received for %s : asked for all config items" % (techno))
                    keys = self._fetch_techno_config(techno, hostname, key).keys()
                    values = self._fetch_techno_config(techno, hostname, key).values()
                    self._send_config(techno, hostname, keys, values)
                else:
                    self.log.debug("New request config received for %s : %s" % (techno, key))
                    self._send_config(techno, hostname, key, self._fetch_techno_config(techno, hostname, key))

    def _send_config(self, technology, hostname, key, value, element = None):
        '''
        Send a config value message for an element's config item
        @param technology : the technology of the element
        @param hostname : hostname
        @param element :  the name of the element
        @param key : the key or list of keys of the config tuple(s) to fetch
        @param value : the value or list of values corresponding to the key(s)
        '''
        self.log.debug("Send config response for %s on %s : %s = %s" % (technology, hostname, key, value))
        mess = XplMessage()
        mess.set_type('xpl-stat')
        mess.set_schema('domogik.config')
        mess.add_data({'technology' :  technology})
        mess.add_data({'hostname' :  hostname})
        if element:
            mess.add_data({'element' :  element})
        # If key/value are lists, then we add a key=value for each item
        if isinstance(key, list):
            for (_key, _val) in zip(key, value):
                mess.add_data({_key :  _val})
        else:
            mess.add_data({key :  value})
        # mess.set_conf_key('target', plugin)
        self.myxpl.send(mess)

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
        # This array is here for information only but is not used anymore
        # Values are now on the database
        print("****** key = %s" % key)
        vals = {'x10': {'heyu-cfg-path':'/etc/heyu/x10.conf',
                        'heyu-file-0': 'TTY /dev/ttyUSB0',
                        'heyu-file-1': 'TTY_AUX /dev/ttyUSB0 RFXCOM',
                        'heyu-file-2': 'ALIAS back_door D5 DS10A 0x677'},
                'global': {'pid-dir-path': '/var/run/'},
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
                try:
                    val = self._db.get_plugin_config(techno, hostname, key).value
                    if val == '':
                        val = "None"
                    return val
                except AttributeError:
                    return "None"
            else:
                vals = self._db.list_plugin_config(techno, hostname)
                res = {}
                for val in vals:
                    if val == '':
                        res[val.key] = "None"
                    else:
                        res[val.key] = val.value
                return res
        except:
            self.log.warn("No config found for technolgy %s on %s, key %s" % (techno, hostname, key))
            return "None"

    def _set_config(self, technology, hostname, key, value):
        '''
        Send a config value message for an element's config item
        @param technology : the technology of the element
        @param hostname : hostname
        @param key : the key to set
        @param value : the value to set
        '''
        self.log.debug("Set config response for %s on %s : %s = %s" % (technology, hostname, key, value))

        try:
            self._db.set_plugin_config(techno, hostname, key, value)
    
            mess = XplMessage()
            mess.set_type('xpl-stat')
            mess.set_schema('domogik.config')
            mess.add_data({'technology' :  technology})
            mess.add_data({'hostname' :  hostname})
            mess.add_data({'key' :  key})
            mess.add_data({'value' :  value})
            self.myxpl.send(mess)
        except:
            traceback.print_exc()
            self.log.warn("Error while setting %s on %s, key %s" % (techno, hostname, key))
            return "None"


if __name__ == "__main__":
    DBC = DBConnector()
