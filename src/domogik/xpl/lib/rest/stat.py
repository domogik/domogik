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
from domogik.common.utils import call_package_conversion
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
    
            # create the dbHelper 
            self._db = DbHelper()

            ### Rest data
            self.handler_params = handler_params
            self.handler_params.append(self._log_stats)
            self.handler_params.append(self._db)
    
            self._event_requests = self.handler_params[0]._event_requests
            self.get_exception = self.handler_params[0].get_exception

            self.stats = None
        except :
            self._log_stats.error("%s" % traceback.format_exc())
    
    def load(self):
        """ (re)load all xml files to (re)create _Stats objects
        """
        self._log_stats.info("Rest Stat Manager loading.... ")
        try:
            # not the first load : clean
            if self.stats != None:
                for x in self.stats:
                    self.myxpl.del_listener(x.get_listener())

            ### Load stats
            # key1, key2 = device_type_id, schema
            self.stats = []
            for sen in self._db.get_all_sensor():
                self._log_stats.debug(sen)
                statparam = self._db.get_xpl_stat_param_by_sensor(sen.id)
                if statparam is None:
                    self._log_stats.error('Corresponding xpl-stat param can not be found for sensor %s' % (sen))
                    continue
                stat = self._db.get_xpl_stat(statparam.xplstat_id)
                if stat is None:
                    self._log_stats.error('Corresponding xpl-stat can not be found for xplstatparam %s' % (statparam))
                    continue
                dev = self._db.get_device(stat.device_id)
                if dev is None:
                    self._log_stats.error('Corresponding device can not be found for xpl-stat %s' % (stat))
                    continue
                # xpl-trig
                self.stats.append(self._Stat(self.myxpl, dev, stat, sen, \
                                  "xpl-trig", self._log_stats, \
                                  self._log_stats, self._db, \
                                  self._event_requests))
                # xpl-stat
                self.stats.append(self._Stat(self.myxpl, dev, stat, sen, \
                                  "xpl-stat", self._log_stats, \
                                  self._log_stats, self._db, \
                                  self._event_requests))
        except:
            self._log_stats.error("%s" % traceback.format_exc())
  
    class _Stat:
        """ This class define a statistic parser and logger instance
        Each instance create a Listener and the associated callbacks
        """

        def __init__(self, xpl, dev, stat, sensor, xpl_type, log_stats, log_stats_unknown, db, event_requests):
            """ Initialize a stat instance 
            @param xpl : A xpl manager instance
            @param dev : A Device reference
            @param stat : A XplStat reference
            @param sensor: A Sensor reference
            @param xpl-type: what xpl-type to listen for
            """
            ### Rest data
            self._event_requests = event_requests
            self._db = db
            self._log_stats = log_stats
            #self._log_stats_unknown = log_stats_unknown
            self._dev = dev
            self._stat = stat
            self._sen = sensor
            
            ### build the filter
            params = {'schema': stat.schema, 'xpltype': xpl_type}
            for p in stat.params:
                if p.static:
                    params[p.key] = p.value
           
            ### start the listener
            self._log_stats.debug("creating listener for %s" % (params))
            self._listener = Listener(self._callback, xpl, params)

        def get_listener(self):
            """ getter for lsitener object
            """
            return self._listener

        def _callback(self, message):
            """ Callback for the xpl message
            @param message : the Xpl message received 
            """
            my_db = DbHelper()
            self._log_stats.debug("Stat received for device %s." \
                    % (self._dev.name))
            current_date = calendar.timegm(time.gmtime())
            device_data = []
            try:
                # find what parameter to store
                for p in self._stat.params:
                    if p.sensor_id is not None:
                        if p.key in message.data:
                            self._log_stats.debug("Key found %s." \
                                % (p.key))
                            value = message.data[p.key]
                            store = True
                            if p.ignore_values:
                                if value in eval(p.ignore_values):
                                    self._log_stats.debug("Value %s is in the ignore list %s, so not storing." \
                                         % (value, p.ignore_values))
                                    store = False
                            if store:
                                # check if we need a conversion
                                if self._sen.conversion is not None and self._sen.conversion == '':
                                    value = call_package_conversion(\
                                                self._log_stats, self._dev.device_type.plugin_id, \
                                                sel._sen.conversion, value)
                                # do the store
                                device_data.append({"value" : value, "sensor": p.sensor_id})
                                my_db.add_sensor_history(p.sensor_id, value, current_date)
            except:
                error = "Error when processing stat : %s" % traceback.format_exc()
                print("==== Error in Stats ====")
                print(error)
                print("========================")
                self._log_stats.error(error)
            # put data in the event queue
            self._event_requests.add_in_queues(self._dev.id, 
                    {"timestamp" : current_date, "device_id" : self._dev.id, "data" : device_data})
            del(my_db)
