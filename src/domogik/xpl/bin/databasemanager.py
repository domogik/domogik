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

Module purpose
==============

Manage connection to the database

Implements
==========

- DBConnector.__init__(self)
- DBConnector._request_config_cb(self, message)
- DBConnector._send_config(self, technology, key, value, module, element = None)
- DBConnector._fetch_elmt_config(self, techno, element, key)
- DBConnector._fetch_techno_config(self, techno, key)
- DBConnector._update_stat(self, message)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.lib.xplconnector import *
from domogik.common.configloader import *

class DBConnector(xPLModule):
    '''
    Manage the connection between database and the xPL stuff
    Should be the *only* object to access the database in the core side
    '''

    def __init__(self):
        '''
        Initialize database and xPL connection
        '''
        xPLModule.__init__(self, 'database_manager')
        self._log = self.get_my_logger()
        self._log.debug("Init database_manager instance")
        self.__myxpl = Manager()
        Listener(self._request_config_cb, self.__myxpl,
                {'schema': 'domogik.config', 'type': 'xpl-cmnd'})
        #cfgloader = Loader('database')
        #config = cfgloader.load()[1]

        #Build database url
#        db_url = "%s://" % config['type']
#        if config['username']:
#            db_url += config['username']
#            if config['password']:
#                db_url += ':%s' % config['password']
#            db_url += '@'
#        db_url += "%s" % config['host']
#        if config['port']:
#            db_url += ':%s' % config['port']
#        db_url += '/%s' % config['db_name']
#
#        db = create_engine(db_url)
#        self._metadata = BoundMetaData(db)
#        self._prefix = config['prefix']
    def _request_config_cb(self, message):
        '''
        Callback to receive a request for some config stuff
        @param message : the xPL message
        '''
        techno = message.get_key_value('technology')
        key = message.get_key_value('key')
        element = message.get_key_value('element')
        if not key:
            self._log.debug("New request config received for %s :\
                    asked for all config items" % (techno))
        else:
            self._log.debug("New request config received for %s : %s" % (techno,
            key))
        if element:
            self._send_config(techno, key, self._fetch_elmt_config(techno,
            element, key), message.get_conf_key_value("source"), element)
        else:
            if not key:
                keys = self._fetch_techno_config(techno, key).keys()
                values = self._fetch_techno_config(techno, key).values()
                self._send_config(techno, keys, values,
                message.get_conf_key_value("source"))
            else:
                self._send_config(techno, key, self._fetch_techno_config(techno,
                key), message.get_conf_key_value("source"))

    def _send_config(self, technology, key, value, module, element = None):
        '''
        Send a config value message for an element's config item
        @param technology : the technology of the element
        @param element :  the name of the element
        @param key : the key or list of keys of the config tuple(s) to fetch
        @param value : the value or list of values corresponding to the key(s)
        @param module : the name of the module which requested the value
        '''
        self._log.debug("Send config response %s : %s" % (key, value))
        mess = Message()
        mess.set_type('xpl-stat')
        mess.set_schema('domogik.config')
        mess.set_data_key('technology', technology)
        if element:
            mess.set_data_key('element', element)
        #If key/value are lists, then we add an key=value for each item
        print "LIST : %s, %s" % (key, isinstance(key, list))
        if isinstance(key, list):
            for (k, v) in zip(key, value):
                print "set data key %s = %s " % (k, v)
                mess.set_data_key(k, v)
        else:
            mess.set_data_key(key, value)
#        mess.set_conf_key('target', module)
        self.__myxpl.send(mess)

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

    def _fetch_techno_config(self, techno, key):
        '''
        Fetch a technology global config value in the database
        @param techno : the technology of the element
        @param key : the key of the config tuple to fetch
        '''
        #TODO : use the database
        vals = {'x10': {'heyu_cfg_path':'/etc/heyu/x10.conf'},
#            'heyu_file_0': 'TTY /dev/ttyUSB0',
 #           'heyu_file_1': 'TTY_AUX /dev/ttyUSB0 RFXCOM',
 #           'heyu_file_2': 'ALIAS back_door D5 DS10A 0x677'},
                'global': {'pid_dir_path': '/tmp/'},
                }
        try:
            if key:
                return vals[techno][key]
            else:
                return vals[techno]
        except:
            return None

    def _update_stat(self, message):
        #TODO
        pass
if __name__ == "__main__":
    d = DBConnector()
