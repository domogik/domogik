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

Log device stats by listening xpl network

Implements
==========

- StatsManager

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from datetime import datetime 
from xml.dom import minidom
import glob

from domogik.xpl.common.plugin import xPLPlugin
from domogik.xpl.common.xplconnector import Listener
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader

class StatsManager(xPLPlugin):
    """
    Listen on the xPL network and keep stats of device and system state
    """
    def __init__(self):
        xPLPlugin.__init__(self, 'statmgr')
        cfg = Loader('domogik')
        config = cfg.load()
        cfg_db = dict(config[1])
        directory = "%s/share/domogik/listeners/" % cfg_db['custom_prefix']

        files = glob.glob("%s/*/*xml" % directory)
        stats = {}
        self._log = self.get_my_logger()
        self._db = DbHelper()

        # See http://wiki.domogik.org/tiki-index.php?page=xPLStatManager&bl=y for xml format
        # Formay of res :
        #{'techno_name': {
        #    'schema_name': {
            #    'xpltype': {
                #    'listener':{
                #       'key1':'value1',
                #       'key2':'value2'
                #     },
                #     'mapping': {
                #       'device':'field1',
                #       'field2':'None',
                #       'field3':'custom_name'
                #     },
            #    },
            #    'xpltype2':{
        #     etc ...
        #   }
        #  },
        #   'schema_name2': [
        #   'xpltype' : {
        #       ...
        #   }
        #  'techno_name2': { 
        #   etc...
        #

        res = {}
        for _file in files :
            self._log.info("Parse file %s" % _file)
            doc = minidom.parse(_file)
            #Statistic/root node
            technology = doc.documentElement.attributes.get("technology").value
            schema_types = self.get_schemas_and_types(doc.documentElement)
            self._log.debug("Parsed : %s" % schema_types)
            for schema in schema_types:
                for type in schema_types[schema]:
                    is_uniq = self.check_config_uniqueness(res, schema, type)
                    if not is_uniq:
                        self._log.warning("Schema %s, type %s is already defined ! check your config." % (schema, type))
                        self.force_leave()
            if technology not in res:
                res[technology] = {}
                stats[technology] = {}
            
            for schema in schema_types:
                if schema not in res[technology]:
                    res[technology][schema] = {}
                    stats[technology][schema] = {}
                for type in schema_types[schema]:
                    device, mapping = self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0])
                    res[technology][schema][type] = {"filter": 
                            self.parse_listener(schema_types[schema][type].getElementsByTagName("listener")[0]),
                            "mapping": mapping,
                            "device": device}
            
                    stats[technology][schema][type] = self._Stat(self._myxpl, res[technology][schema][type], technology, schema, type, self._db, self._log)

    def get_schemas_and_types(self, node):
        """ Get the schema and the xpl message type
        @param node : the root (statistic) node
        @return {'schema1': ['type1','type2'], 'schema2', ['type1','type3']}
        """
        res = {}
        schemas = node.getElementsByTagName("schema")
        for schema in schemas:
            res[schema.attributes.get("name").value] = {}
            for xpltype in schema.getElementsByTagName("xpltype"):
                res[schema.attributes.get("name").value][xpltype.attributes.get("type").value] = xpltype
        return res

    def check_config_uniqueness(self, res, schema, type):
        """ Check the schema/type is not already defined in res
        @param res : the array with all already-defined mapping
        @param schema : the current schema
        @param type : the current xpl-type
        Return True if the schema/type is *not* already defined in res
        """
        print res
        for techno in res.keys():
            for _schema in res[techno].keys(): 
                if _schema == schema:
                    for _type in res[techno][schema].keys():
                        if _type == type:
                            return False
        return True

    def parse_listener(self, node):
        """ Parse the "listener" node
        """
        filters = {}
        for _filter in node.getElementsByTagName("filter")[0].getElementsByTagName("key"):
            filters[_filter.attributes["name"].value] = _filter.attributes["value"].value
        return filters
        
    def parse_mapping(self, node):
        """ Parse the "mapping" node
        """
        values = {}
        device = node.getElementsByTagName("device")[0].attributes["field"].value.lower()
        for value in node.getElementsByTagName("value"):
            #If a "name" attribute is defined, use it as vallue, else value is empty
            if value.attributes.has_key("name"):
                values[value.attributes["field"].value] = value.attributes["name"].value.lower()
            else:
                values[value.attributes["field"].value] = None
        return device, values


    class _Stat:
        """ This class define a statistic parser and logger instance
        Each instance create a Listener and the associated callbacks
        """

        def __init__(self, xpl, res, technology, schema, type, database, log):
            """ Initialize a stat instance 
            @param xpl : A xpl manager instance
            @param res : The result of xml parsing for this techno/schema/type
            @params technology : The technology monitored
            @param schema : the schema to listen for
            @param type : the xpl type to listen for
            @param db : a DbHelper instance 
            @param log : the plugin logger (from self.get_my_logger())
            """
            self._res = res
            self._db = database
            params = {'schema':schema, 'xpltype': type}
            params.update(res["filter"])
            self._listener = Listener(self._callback, xpl, params)
            self._log = log
            self._technology = technology

        def _callback(self, message):
            """ Callback for the xpl message
            @param message : the Xpl message received 
            """
            self._db = DbHelper()
            self._log.debug("message catcher : %s" % message)
            d_id = self._db.get_device_by_technology_and_address(self._technology, \
                    message.data[self._res["device"]]).id
            if d_id == None:
                self._log.warning("Received a stat for an unreferenced device : %s - %s" \
                        % (self._technology, message.data[self._res["device"]]))
                return
            else:
                self._log.debug("Stat received for %s - %s." \
                        % (self._technology, message.data[self._res["device"]]))
                datas = {}
                timestamp = datetime.today()
                for key in self._res["mapping"].keys():
                    if message.data.has_key(key):
                        #Check if a name has been chosen for this value entry
                        if self._res["mapping"][key] == None:
                            #If not, keep the one from message
                            self._db.add_device_stat(timestamp, key, message.data[key], d_id)
                        else:
                            self._db.add_device_stat(timestamp, self._res["mapping"][key], message.data[key], d_id)

def main():
    StatsManager()

if __name__ == "__main__":
    main()
