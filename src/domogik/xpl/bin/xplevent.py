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
=============

Implements
==========

class StatsManager(XplPlugin):

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.database import DbHelper
from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.mq.pubsub.publisher import MQPub 
from domogik.mq.reqrep.worker import MQRep
from domogik.mq.message import MQMessage
import time
from Queue import Queue, Empty, Full
import traceback
import datetime
import calendar
import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.common.utils import call_package_conversion

################################################################################
class XplEvent(XplPlugin, MQRep):
    """ Statistics manager
    """
    
    def __init__(self):
        """ Initiate DbHelper, Logs and config
        """
        XplPlugin.__init__(self, 'xplevent')
        MQRep.__init__(self, zmq.Context(), 'xplevent')
        self.log.info("XPL Events manager initialisation...")
        self._db = DbHelper()
        self.pub = MQPub(zmq.Context(), 'xplevent')
        self.stats = None
        self.load()
        self.enable_hbeat()
        IOLoop.instance().start()

    def on_mdp_request(self, msg):
        if msg._action == "reload":
            self.load()
            msg = MQMessage()
            msg.setaction( 'reload.result' )
            self.reply(msg.get())

    def load(self):
        """ (re)load all xml files to (re)create _Stats objects
        """
        self.log.info("Rest Stat Manager loading.... ")
        try:
            # not the first load : clean
            if self.stats != None:
                self.log.info("reloading")
                for x in self.stats:
                    self.myxpl.del_listener(x.get_listener())

            ### Load stats
            # key1, key2 = device_type_id, schema
            self.stats = []
            for sen in self._db.get_all_sensor():
                self.log.debug(sen)
                statparam = self._db.get_xpl_stat_param_by_sensor(sen.id)
                if statparam is None:
                    self.log.error('Corresponding xpl-stat param can not be found for sensor %s' % (sen))
                    continue
                stat = self._db.get_xpl_stat(statparam.xplstat_id)
                if stat is None:
                    self.log.error('Corresponding xpl-stat can not be found for xplstatparam %s' % (statparam))
                    continue
                dev = self._db.get_device(stat.device_id)
                if dev is None:
                    self.log.error('Corresponding device can not be found for xpl-stat %s' % (stat))
                    continue
                # xpl-trig
                self.stats.append(self._Stat(self.myxpl, dev, stat, sen, \
                                  "xpl-trig", self.log, self._db, self.pub))
                # xpl-stat
                self.stats.append(self._Stat(self.myxpl, dev, stat, sen, \
                                  "xpl-stat", self.log, self._db, self.pub))
        except:
            self.log.error("%s" % traceback.format_exc())
        self.log.info("Loading finished")
  
    class _Stat:
        """ This class define a statistic parser and logger instance
        Each instance create a Listener and the associated callbacks
        """

        def __init__(self, xpl, dev, stat, sensor, xpl_type, log_stats, db, pub):
            """ Initialize a stat instance 
            @param xpl : A xpl manager instance
            @param dev : A Device reference
            @param stat : A XplStat reference
            @param sensor: A Sensor reference
            @param xpl-type: what xpl-type to listen for
            """
            ### Rest data
            self._db = db
            self._log_stats = log_stats
            self._dev = dev
            self._stat = stat
            self._sen = sensor
            self._pub = pub
            
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
                            value = message.data[p.key]
                            self._log_stats.debug("Key found %s with value %s." \
                                % (p.key, value))
                            store = True
                            if p.ignore_values:
                                if value in eval(p.ignore_values):
                                    self._log_stats.debug("Value %s is in the ignore list %s, so not storing." \
                                         % (value, p.ignore_values))
                                    store = False
                            if store:
                                # check if we need a conversion
                                if self._sen.conversion is not None and self._sen.conversion != '':
                                    value = call_package_conversion(\
                                                self._log_stats, self._dev.device_type.plugin_id, \
                                                self._sen.conversion, value)
                                    self._log_stats.debug("Key found %s with value %s after conversion." \
                                        % (p.key, value))
                                # do the store
                                device_data.append({"value" : value, "sensor": p.sensor_id})
                                my_db.add_sensor_history(p.sensor_id, value, current_date)
            except:
                error = "Error when processing stat : %s" % traceback.format_exc()
                print("==== Error in Stats ====")
                print(error)
                print("========================")
                self._log_stats.error(error)
            # publish the result
            self._pub.send_event('device-stats', \
                          {"timestamp" : current_date, "device_id" : self._dev.id, "data" : device_data})
            # put data in the event queue
            #self._event_requests.add_in_queues(self._dev.id, 
            #        {"timestamp" : current_date, "device_id" : self._dev.id, "data" : device_data})
            del(my_db)

if __name__ == '__main__':
    EVTN = XplEvent()
