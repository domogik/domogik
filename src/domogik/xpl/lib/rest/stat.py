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
=============

- Log device stats by listening xpl network

Implements
==========

StatsManager object


@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.common import logger
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader
from xml.dom import minidom
import time
import datetime
import traceback
import glob
import calendar


class StatsManager:
    """
    Listen on the xPL network and keep stats of device and system state
    """
    def __init__(self, handler_params, xpl):
        """ 
        @param handler_params : The server params 
        @param xpl : A xPL Manager instance 
        """

        try:
            self.myxpl = xpl

            # logging initialization
            log = logger.Logger('rest-stat')
            self._log_stats = log.get_logger('rest-stat')
            self._log_stats.info("Rest Stat Manager initialisation...")
    
            # logging initialization for unkwnon devices
            log_unknown = logger.Logger('rest-stat-unknown-devices')
            self._log_stats_unknown = log_unknown.get_logger('rest-stat-unknown-devices')
    
            # config
            cfg = Loader('domogik')
            config = cfg.load()
            cfg_db = dict(config[1])
            # plugin installation path
            if cfg_db.has_key('package_path'):
                self._package_path = cfg_db['package_path']
                self._log_stats.info("Set package path to '%s' " % self._package_path)
                print("Set package path to '%s' " % self._package_path)
                self.directory = "%s/domogik_packages/stats/" % self._package_path
            else:
                self._log_stats.info("No package path defined in config file")
                self._package_path = None
                self.directory = "%s/share/domogik/stats/" % cfg_db['src_prefix']

            self._db = DbHelper()

            ### Rest data
            self.handler_params = handler_params
            self.handler_params.append(self._log_stats)
            self.handler_params.append(self._log_stats_unknown)
            self.handler_params.append(self._db)
    
            self._event_requests = self.handler_params[0]._event_requests
            self.get_exception = self.handler_params[0].get_exception

            self.stats = None

            ### list of loaded and KO xml files
            self.xml_date = None
            self.xml = []
            self.xml_ko = []

        except :
            self._log_stats.error("%s" % traceback.format_exc())
    
    def get_xml_list(self):
        """ getter for loaded xml files
        """
        return self.xml

    def get_xml_ko_list(self):
        """ getter for bad xml files
        """
        return self.xml_ko

    def get_load_date(self):
        """ getter for xml last load date
        """
        return self.xml_date

    def load(self):
        """ (re)load all xml files to (re)create _Stats objects
        """
        try:
            self.xml_date = datetime.datetime.now()
            self.xml = []
            self.xml_ko = []

            ### Clean old _Stat objects ans created Listeners
            # not the first load : clean
            if self.stats != None:
                for cl_techno in self.stats:
                    for cl_message in self.stats[cl_techno]:
                        for cl_type in self.stats[cl_techno][cl_message]:
                             self.myxpl.del_listener(self.stats[cl_techno][cl_message][cl_type].get_listener())

            ### Load files
            files = glob.glob("%s/*/*xml" % self.directory)
            self.stats = {}
    
            ### Read xml files
            res = {}
            for _file in files :
                if _file[-4:] == ".xml":
                    try:
                        self._log_stats.info("Parse file %s" % _file)
                        doc = minidom.parse(_file)
                        #Statistic/root node
                        technology = doc.documentElement.attributes.get("technology").value
                        schema_types = self.get_schemas_and_types(doc.documentElement)
                        self._log_stats.debug("Parsed : %s" % schema_types)
                        if technology not in res:
                            res[technology] = {}
                            self.stats[technology] = {}
                        
                        for schema in schema_types:
                            if schema not in res[technology]:
                                res[technology][schema] = {}
                                self.stats[technology][schema] = {}
                            for xpl_type in schema_types[schema]:
                                device, mapping, static_device, device_type = self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0])
                                res[technology][schema][xpl_type] = {"filter": 
                                        self.parse_listener(schema_types[schema][xpl_type].getElementsByTagName("listener")[0]),
                                        "mapping": mapping,
                                        "device": device,
                                        "static_device": static_device,
                                        "device_type": device_type}
                        
                                self.stats[technology][schema][xpl_type] = self._Stat(self.myxpl, res[technology][schema][xpl_type], technology, schema, xpl_type, self._log_stats, self._log_stats_unknown, self._db, self._event_requests)
                                self._log_stats.info("One listener created")
                        self.xml.append(_file)
                    except:
                        self._log_stats.error("Error loading xml files '%s' : %s" % (_file, traceback.format_exc()))
                        self.xml_ko.append(_file)
        except :
            self._log_stats.error("%s" % traceback.format_exc())

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
                if xpltype.attributes.get("type").value == "*":
                    res[schema.attributes.get("name").value]["xpl-trig"] = xpltype
                    res[schema.attributes.get("name").value]["xpl-stat"] = xpltype
                else:
                    res[schema.attributes.get("name").value][xpltype.attributes.get("type").value] = xpltype
        return res

    def parse_listener(self, node):
        """ Parse the "listener" node
        """
        filters = {}
        for _filter in node.getElementsByTagName("filter")[0].getElementsByTagName("key"):
            if _filter.attributes["name"].value in filters:
                if not isinstance(filters[_filter.attributes["name"].value], list):
                    filters[_filter.attributes["name"].value] = \
                            [filters[_filter.attributes["name"].value]]
                filters[_filter.attributes["name"].value].append(_filter.attributes["value"].value)
            else:
                filters[_filter.attributes["name"].value] = _filter.attributes["value"].value
        return filters

    def parse_mapping(self, node):
        """ Parse the "mapping" node
        """
         
        values = []
        device_node = node.getElementsByTagName("device")[0]
        device = None
        static_device = None
        device_type = None
        if device_node.attributes.has_key("field"):
            device = device_node.attributes["field"].value.lower()
        elif device_node.attributes.has_key("static_name"):
            static_device = device_node.attributes["static_name"].value.lower()
        elif device_node.attributes.has_key("type"):
            device_type = device_node.attributes["type"].value.lower()
 
        #device = node.getElementsByTagName("device")[0].attributes["field"].value.lower()
        for value in node.getElementsByTagName("value"):
            name = value.attributes["field"].value
            data = {}
            data["name"] = name
            #If a "name" attribute is defined, use it as vallue, else value is empty
            if value.attributes.has_key("history_size"):
                data["history_size"] = int(value.attributes["history_size"].value)
            else:
                data["history_size"] = 0
            if value.attributes.has_key("new_name"):
                data["new_name"] = value.attributes["new_name"].value.lower()
                if value.attributes.has_key("filter_key"):
                    data["filter_key"] = value.attributes["filter_key"].value.lower()
                    if value.attributes.has_key("filter_value"):
                        data["filter_value"] = value.attributes["filter_value"].value.lower()
                    else:
                        data["filter_value"] = None
                else:
                    data["filter_key"] = None
                    data["filter_value"] = None
            else:
                data["new_name"] = None
                data["filter_key"] = None
                data["filter_value"] = None
            values.append(data)
        return device, values, static_device, device_type


    class _Stat:
        """ This class define a statistic parser and logger instance
        Each instance create a Listener and the associated callbacks
        """

        def __init__(self, xpl, res, technology, schema, xpl_type, log_stats, log_stats_unknown, db, event_requests):
            """ Initialize a stat instance 
            @param xpl : A xpl manager instance
            @param res : The result of xml parsing for this techno/schema/type
            @params technology : The technology monitored
            @param schema : the schema to listen for
            @param xpl_type : the xpl type to listen for
            @param handler_params : handler_params from rest
            """
            ### Rest data
            self._event_requests = event_requests
            self._db = db
            self._log_stats = log_stats
            self._log_stats_unknown = log_stats_unknown

            self._res = res
            params = {'schema':schema, 'xpltype': xpl_type}
            params.update(res["filter"])
            self._listener = Listener(self._callback, xpl, params)
            self._technology = technology

        def get_listener(self):
            """ getter for lsitener object
            """
            return self._listener

        def _callback(self, message):
            """ Callback for the xpl message
            @param message : the Xpl message received 
            """

            ### we put data in database
            my_db = DbHelper()
            self._log_stats.debug("message catcher : %s" % message)
            try:
                if self._res["device"] != None:
                    try:
                        device = message.data[self._res["device"]]
                    except KeyError:
                        # key error means that we are trying to get some key from a xpl where there is no such key
                        # there may be an issue in the xml file!
                        self._log_stats.error("Key error : %s in the message : %s" % (self._res["device"], message))
                        return
                    my_device = my_db.get_device_by_technology_and_address(self._technology, \
                        message.data[self._res["device"]])
                    if my_device != None:
                        d_id = my_device.id
                    else:
                        raise AttributeError
                    #d_id = my_db.get_device_by_technology_and_address(self._technology, \
                    #    message.data[self._res["device"]]).id
                    device = message.data[self._res["device"]]
                elif self._res["static_device"] != None:
                    d_id = my_db.get_device_by_technology_and_address(self._technology, \
                        self._res["static_device"]).id
                    device = self._res["static_device"]
                elif self._res["device_type"] != None:
                    # device id equals 0 for a notification
                    if self._res["device_type"] == "notification":
                        d_id = 0
                        device = "notification"
                else:  # oups... something wrong in xml file ?
                    self._log_stats.error("Device has no name... is there a problem in xml file ?")
                    raise AttributeError
                #print("Stat for techno '%s' / adress '%s' / id '%s'" % (self._technology, message.data[self._res["device"]], d_id))
                #print("Stat for techno '%s' / adress '%s' / id '%s'" % (self._technology, device, d_id))
            except AttributeError:
                if self._res["device"] != None:
                    self._log_stats_unknown.debug("Received a stat for an unreferenced device : %s - %s" \
                        % (self._technology, message.data[self._res["device"]]))
                else:
                    self._log_stats_unknown.debug("Received a stat for an unreferenced device : %s - %s" \
                        % (self._technology, self._res["static_device"]))
                print("=> unknown device")
                del(my_db)
                return
            #self._log_stats.debug("Stat received for %s - %s." \
            #        % (self._technology, message.data[self._res["device"]]))
            self._log_stats.debug("Stat received for %s - %s." \
                    % (self._technology, device))
            current_date = calendar.timegm(time.gmtime())
            device_data = []

            ### mapping processing
            for my_map in self._res["mapping"]:
                # first : get value and default key
                key = my_map["name"]
                history_size = my_map["history_size"]
                try:
                    value = message.data[my_map["name"]].lower()
                    if my_map["filter_key"] == None:
                        key = my_map["name"]
                        device_data.append({"key" : key, "value" : value})
                        # we don't insert notifications
                        if d_id != 0:
                            my_db.add_device_stat(current_date, key, value, \
                                                  d_id, \
                                                  history_size)
                    else:
                        if my_map["filter_value"] != None and \
                           my_map["filter_value"].lower() == message.data[my_map["filter_key"]].lower():
                            key = my_map["new_name"]
                            device_data.append({"key" : key, "value" : value})
                            # we don't insert notifications
                            if d_id != 0:
                                my_db.add_device_stat(current_date, key, \
                                                  value, \
                                                  d_id, history_size)
                        else:
                            if my_map["filter_value"] == None:
                                self._log_stats.warning ("Stats : no filter_value defined in map : %s" % str(my_map))
                except KeyError:
                    # no value in message for key
                    # example : a x10 command = ON has no level value
                    print("No param value in message for key")
                except:
                    error = "Error when processing stat : %s" % traceback.format_exc()
                    print("==== Error in Stats ====")
                    print(error)
                    print("========================")
                    self._log_stats.error(error)
    
            # Put data in events queues
            self._event_requests.add_in_queues(d_id, 
                    {"timestamp" : current_date, "device_id" : d_id, "data" : device_data})
            del(my_db)





