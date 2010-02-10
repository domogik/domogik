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

from domogik.xpl.lib.module import xPLModule
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader
from domogik.xpl.lib.xplconnector import *

class StatsManager(xPLModule):
    """
    Listen on the xPL network and keep stats of device and system state
    """
    def __init__(self):
        xPLModule.__init__(self, 'statmgr')
        cfg = Loader('domogik')
        config = cfg.load()
        db = dict(config[1])
        directory = "%s/share/domogik/listeners/" % db['custom_prefix']

        files = glob.glob("%s/*xml" % directory)
        stats = {}
        self._log = self.get_my_logger()
        self._db = DbHelper()

        # 
        #<?xml version="1.0" encoding="UTF-8"?>  
        #<statistic technology="plcbus"> <!-- Element racine -->
        #    <listener> <!-- défini les paramètres de filtrage du listener -->
        #        <schema>control.basic</schema>
        #        <xpltype>xpl-trig</xpltype>
        #        <filter>
        #            <key name="type" value="plcbus" />
        #            <key name="command" value="on" />
        #        </filter>
        #    </listener>
        #    <mapping> <!-- défini le mapping entre les clés du message et la bdd -->
        #        <device field="device"/> <!-- define the device name -->
        #        <!-- The value node can have 2 attributes :
        #            - field : mandatory ! define the key of the pair key=value to get in the Xpl message 
        #            - name : optionnal, if it's define, the 'name' of this value entry will be the value defined,
        #                    else it will be the filed name.
        #        -->
        #        <value field="command"/>
        #        <value field="command" name="bar" />
        #    </mapping>
        #</statistic>

        for file in files :
            self._log.info("Parse file %s" % file)
            doc = minidom.parse(file)
            res = {}
            res["technology"] = doc.documentElement.attributes.get("technology").value
            res.update(self.parse_listener(doc.documentElement.getElementsByTagName("listener")[0]))
            res.update(self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0]))
            stat = self.__Stat(self._myxpl, res, self._db, self._log)
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

        def __init__(self, xpl, res, db, log):
            """ Initialize a stat instance 
            @param xpl : A xpl manager instance
            @param res : The result of xml parsing
            @param db : a DbHelper instance 
            @param log : the module logger (from self.get_my_logger())
            """
            self._res = res
            self._db = db
            params = {'schema':res["schema"], 'xpltype':res["xpltype"]}
            params.update(res["filter"])
            self._listener = Listener(self._callback, xpl, params)
            self._log = log

        def _callback(self, message):
            """ Callback for the xpl message
            @param message : the Xpl message received 
            """
            self._log.debug("message catcher : %s" % message)
            d_id = self._db.get_device_by_technology_and_address(self._res["technology"], \
                    message.data[self._res["device"])
            if d_id == None:
                self._log.warning("Received a stat for an unreferenced device : %s - %s" \
                        % (self._res["technology"], message.data[self._res["device"]))
                return
            else:
                self._log.debug("Stat received for %s - %s." \
                        % (self._res["technology"], message.data[self._res["device"]))
                datas = {}
                for key in self._res["values"].keys():
                    if message.data.has_key(key):
                        #Check if a name has been chosen for this value entry
                        if self._res["values"][key] == None:
                            #If not, keep the one from message
                            datas[key] = message.data[key]
                        else:
                            datas[self._res["values"][key]] = message.data[key]
                self._db.add_device_stat(d_id, datetime.today(), datas)

if __name__ == "__main__":
    s = StatsManager()
