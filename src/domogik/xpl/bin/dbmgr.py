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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.database import DbHelper
import time

DATABASE_CONNECTION_NUM_TRY = 50
DATABASE_CONNECTION_WAIT = 30

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

        # Check for database connexion
        self._db = DbHelper()
        nb_test = 0
        db_ok = False
        while not db_ok and nb_test < DATABASE_CONNECTION_NUM_TRY:
            nb_test += 1
            try:
                self._db.list_user_accounts()
                db_ok = True
            except:
                msg = "The database is not responding. Check your configuration of if the database is up. Test %s/%s" % (nb_test, DATABASE_CONNECTION_NUM_TRY)
                print(msg)
                self.log.error(msg)
                msg = "Waiting for %s seconds" % DATABASE_CONNECTION_WAIT
                print(msg)
                self.log.info(msg)
                time.sleep(DATABASE_CONNECTION_WAIT)

        if nb_test >= DATABASE_CONNECTION_NUM_TRY:
            msg = "Exiting dbmgr!"
            print(msg)
            self.log.error(msg)
            self.force_leave()
            return

        msg = "Connected to the database"
        print(msg)
        self.log.info(msg)
        try:
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
        #try:
        self._db = DbHelper(engine=self._engine)
        techno = message.data['technology']
        hostname = message.data['hostname']
        key = message.data['key']
        msg = "Request  h=%s, t=%s, k=%s" % (hostname, techno, key)
        print(msg)
        self.log.debug(msg)
        if "value" in message.data:
            new_value = message.data['value']
        else:
            new_value = None
        if "element" in message.data:
            element = message.data['element']
        else:
            element = None

        msg = "Request  h=%s, t=%s, k=%s (2)" % (hostname, techno, key)
        print(msg)
        self.log.debug(msg)
        # Set configuration
        if new_value:
            msg = "Set config h=%s, t=%s, k=%s, v=%s" % (hostname, techno, key, new_value)
            print msg
            self.log.debug(msg)
            self._set_config(techno, hostname, key, new_value)

        # Send configuration
        else:
            msg = "Request  h=%s, t=%s, k=%s (send)" % (hostname, techno, key)
            print(msg)
            self.log.debug(msg)
            if element:
                msg = "Request  h=%s, t=%s, k=%s (send if element)" % (hostname, techno, key)
                print(msg)
                self.log.debug(msg)
                self._send_config(techno, hostname, key, self._fetch_elmt_config(techno, element, key), element)
            else:
                msg = "Request  h=%s, t=%s, k=%s (send else)" % (hostname, techno, key)
                print(msg)
                self.log.debug(msg)
                if not key:
                    msg = "Request  h=%s, t=%s, k=%s (send if not key)" % (hostname, techno, key)
                    print(msg)
                    self.log.debug(msg)
                    keys = self._fetch_techno_config(techno, hostname, key).keys()
                    values = self._fetch_techno_config(techno, hostname, key).values()
                    self._send_config(techno, hostname, keys, values)
                else:
                    msg = "Request  h=%s, t=%s, k=%s (send else of if not key)" % (hostname, techno, key)
                    print(msg)
                    self.log.debug(msg)
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
        msg = "Response h=%s, t=%s, k=%s, v=%s" % (hostname, technology, key, value)
        print(msg)
        self.log.debug(msg)
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
        #vals = {'x10': {'heyu-cfg-path':'/etc/heyu/x10.conf',
        #                'heyu-file-0': 'TTY /dev/ttyUSB0',
        #                'heyu-file-1': 'TTY_AUX /dev/ttyUSB0 RFXCOM',
        #                'heyu-file-2': 'ALIAS back_door D5 DS10A 0x677'},
        #        'global': {'pid-dir-path': '/var/run/'},
        #        'onewire': {'temperature_refresh_delay' : '10'},
        #        'cidmodem': {'device' : '/dev/ttyUSB1',
        #                   'nbmaxtry' : '10',
        #                   'interval' : '15'},
        #        'mirror': {'device' : '/dev/hidraw0',
        #                   'nbmaxtry' : '10',
        #                   'interval' : '15'},
        #        'xbmc_not': {'address' : '192.168.0.20:8080',
        #                 'delay' : '15',
        #                 'maxdelay' : '20'},
        #        'gagenda': {'email' : "fritz.smh@gmail.com",
        #                 'password' : 'XXXXXXXX',
        #                 'calendarname' : 'fritz.smh@gmail.com',
        #                 'startup-plugin':'True'},
        #        'teleinfo' : {'device' : '/dev/teleinfo',
        #            'interval' : '30'},
        #            'dawndusk' : {'startup-plugin':'True'},
        #            'plcbus' : {'device':'/dev/ttyUSB0'},
        #        }
        self.log.debug("FTC 1")
        try:
            if key:
                self.log.debug("FTC 2")
                try:
                    self.log.debug("Get plg conf for %s / %s / %s" % (techno, hostname, key))
                    result = self._db.get_plugin_config(techno, hostname, key)
                    # tricky loop as workaround for a (sqlalchemy?) bug :
                    # sometimes the given result is for another plugin/key
                    # so while we don't get the good data, we loop
                    # This bug happens rarely
                    while result.id != techno or \
                       result.hostname != hostname or \
                       result.key != key:
                        self.log.debug("Bad result : %s/%s != %s/%s" % (result.id, result.key, technology, key))
                        result = self._db.get_plugin_config(techno, hostname, key)
                    self.log.debug("Get plg conf for %s / %s / %s Result=%s" % (techno, hostname, key, result))
                    val = result.value
                    self.log.debug("Get plg conf for %s / %s / %s = %s" % (techno, hostname, key, val))
                    if val == '':
                        val = "None"
                    self.log.debug("Get plg conf for %s / %s / %s = %s (2)" % (techno, hostname, key, val))
                    return val
                except AttributeError:
                    self.log.debug("Attribute error for %s / %s / %s" % (techno, hostname, key))
                    return "None"
            else:
                self.log.debug("FTC 3")
                vals = self._db.list_plugin_config(techno, hostname)
                res = {}
                for val in vals:
                    if val == '':
                        res[val.key] = "None"
                    else:
                        res[val.key] = val.value
                return res
        except:
            msg = "No config found h=%s, t=%s, k=%s" % (hostname, techno, key)
            print(msg)
            self.log.warn(msg)
            return "None"

    def _set_config(self, technology, hostname, key, value):
        '''
        Send a config value message for an element's config item
        @param technology : the technology of the element
        @param hostname : hostname
        @param key : the key to set
        @param value : the value to set
        '''

        try:
            self._db.set_plugin_config(technology, hostname, key, value)
    
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
            msg = "Error while setting h=%s, t=%s, k=%s, v=%s" % (hostname, techno, key, value)
            print(msg)
            self.log.warn(msg)
            return "None"


if __name__ == "__main__":
    DBC = DBConnector()
