#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy:$
# $LastChangedDate:$
# $LastChangedRevision:$

from domogik.xpl.lib.xplconnector import *
from domogik.common.configloader import *
#from sqlalchemy import *


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
        self._log.debug("New request config received for %s : %s" % (techno,
        key))
        if element:
            self._send_config(techno, key, self._fetch_elmt_config(techno,
            element, key), message.get_conf_key_value("source"), element)
        else:
            self._send_config(techno, key, self._fetch_techno_config(techno,
            key), message.get_conf_key_value("source"))

    def _send_config(self, technology, key, value, module, element = None):
        '''
        Send a config value message for an element's config item
        @param technology : the technology of the element
        @param element :  the name of the element
        @param key : the key of the config tuple to fetch
        @param value : the value corresponding to the key
        @param module : the name of the module which requested the value
        '''
        self._log.debug("Send config response %s : %s" % (key, value))
        mess = Message()
        mess.set_type('xpl-stat')
        mess.set_schema('domogik.config')
        mess.set_data_key('technology', technology)
        if element:
            mess.set_data_key('element', element)
        mess.set_data_key('key', key)
        mess.set_data_key('value', value)
        mess.set_conf_key('target', module)
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
        vals = {'x10': {},
                'global': {'pid_dir_path': '/tmp/'},
                }
        try:
            return vals[techno][key]
        except:
            return None

    def _update_stat(self, message):
        #TODO
        pass
if __name__ == "__main__":
    d = DBConnector()
