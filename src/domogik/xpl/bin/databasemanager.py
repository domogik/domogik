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

from datetime import datetime 
from xml.dom import minidom
import glob

from domogik.xpl.lib.xplconnector import *
from domogik.xpl.lib.module import xPLModule
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import *
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader

class DBConnector(xPLModule):
    '''
    Manage the connection between database and the xPL stuff
    Should be the *only* object to access the database in the core side
    '''

    def __init__(self):
        '''
        Initialize database and xPL connection
        '''
        xPLModule.__init__(self, 'dbmgr')
        self._log = self.get_my_logger()
        self._log.debug("Init database_manager instance")
        
        self._db = DbHelper()
        self._stats = StatsManager()
        Listener(self._request_config_cb, self._myxpl,
                {'schema': 'domogik.config', 'xpltype': 'xpl-cmnd'})

    def _request_config_cb(self, message):
        '''
        Callback to receive a request for some config stuff
        @param message : the xPL message
        '''
        #try:
        techno = message.data['technology']
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
            self._send_config(techno, key, self._fetch_elmt_config(techno,
            element, key), message.source, element)
        else:
            if not key:
                keys = self._fetch_techno_config(techno, key).keys()
                values = self._fetch_techno_config(techno, key).values()
                self._send_config(techno, keys, values,
                message.source)
            else:
                self._send_config(techno, key, self._fetch_techno_config(techno,
                key), message.source)
        #except KeyError:
         #   self._log.warning("A request for configuration has been received, but it was misformatted")

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
        mess = XplMessage()
        mess.set_type('xpl-stat')
        mess.set_schema('domogik.config')
        mess.add_data({'technology' :  technology})
        if element:
            mess.add_data({'element' :  element})
        #If key/value are lists, then we add a key=value for each item
        if isinstance(key, list):
            for (k, v) in zip(key, value):
                mess.add_data({k :  v})
        else:
            mess.add_data({key :  value})
#        mess.set_conf_key('target', module)
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

    def _fetch_techno_config(self, techno, key):
        '''
        Fetch a technology global config value in the database
        @param techno : the technology of the element
        @param key : the key of the config tuple to fetch
        '''
        #TODO : use the database
        vals = {'x10': {'heyu-cfg-path':'/etc/heyu/x10.conf',
            'heyu-file-0': 'TTY /dev/ttyUSB0',
            'heyu-file-1': 'TTY_AUX /dev/ttyUSB0 RFXCOM',
            'heyu-file-2': 'ALIAS back_door D5 DS10A 0x677'},
                'global': {'pid-dir-path': '/tmp/'},
                'onewire': {'temperature_refresh_delay' : '10'},
                'calleridmodem': {'device' : '/dev/ttyUSB1',
                           'nbmaxtry' : '10',
                           'interval' : '15'},
                'mirror': {'device' : '/dev/hidraw0',
                           'nbmaxtry' : '10',
                           'interval' : '15'},
                'xbmc': {'address' : '192.168.0.20:8080'},
                'teleinfo' : {'device' : '/dev/ttyUSB0',
                    'interval' : '30'},
                }
        try:
            if key:
                return vals[techno][key]
            else:
                return vals[techno]
        except:
            return None


class StatsManager(xPLModule):
    """
    Listen on the xPL network and keep stats of device and system state
    """
    def __init__(self):
        xPLModule.__init__(self, 'statmgr')
        cfg = Loader('domogik')
        config = cfg.load()
        db = dict(config[1])
        directory = "%s/xml" % db['cfg_path']
        files = glob.glob("%s/*xml" % directory)
        stats = {}
        self._log = self.get_my_logger()

        for file in files :
            self._log.info("Parse file %s" % file)
            doc = minidom.parse(file)
            res = {}
            res["technology"] = doc.documentElement.attributes.get("technology").value
            res.update(self.parse_listener(doc.documentElement.getElementsByTagName("listener")[0]))
            res.update(self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0]))
            stat = self.__Stat(self._myxpl, res)
            stats[file] = stat

    def parse_listener(self,node):
        """ Parse the "listener" node
        """
        res = {}
        res["schema"] = node.getElementsByTagName("schema")[0].firstChild.nodeValue
        res["xpltype"] = node.getElementsByTagName("xpltype")[0].firstChild.nodeValue
        filters = {}
        for filter in node.getElementsByTagName("filter")[0].getElementsByTagName("key"):
            filters[filter.attributes["name"].value] = filter.attributes["value"].value
        res["filter"] = filters
        return res
        
    def parse_mapping(self,node):
        """ Parse the "mapping" node
        """
        res = {}
        res["device"] = node.getElementsByTagName("device")[0].attributes["field"].value
        values = {}
        for value in node.getElementsByTagName("value"):
            #If a "name" attribute is defined, use it as vallue, else value is empty
            if value.attributes.has_key("name"):
                values[value.attributes["field"].value] = value.attributes["name"].value
            else:
                values[value.attributes["field"].value] = None
        res["values"] = values
        return res


    class __Stat:
        """ This class define a statistic parser and logger instance
        Each instance create a Listener and the associated callbacks
        """

        def __init__(self, xpl, res):
            """ Initialize a stat instance 
            @param xpl : A xpl manager instance
            @param res : The result of xml parsing
            """
            self._res = res
            params = {'schema':res["schema"], 'xpltype':res["xpltype"]}
            params.update(res["filter"])
            self._listener = Listener(self._callback, xpl, params)

        def _callback(self, message):
            """ Callback for the xpl message
            @param message : the Xpl message received 
            """
            dbhelper = DbHelper()
            techno_id = self.__self.__dbhelper.get_device_technology_by_name(self._res["technology"]).id
            d_id = self.__dbhelper.search_devices(technology = techno_id, name =
                    message.data[self._res['device']])[0].id
            dbhelper.add_device_stat(d_id, datetime.today(), self._res["values"])


if __name__ == "__main__":
    d = DBConnector()
