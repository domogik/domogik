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

xPL Dawndusk client

Implements
==========
Class dawndusk
- dateFromTuple(tuple)
- get_dawn(message)
- get_dusk(message)

@author: Sébastien Gallet <sgallet@gmail.com>
@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.plugin import XplPlugin
import datetime
#from datetime import timedelta
#from datetime import datetime
from domogik_packages.xpl.lib.dawndusk import DawnduskAPI
from domogik_packages.xpl.lib.dawndusk import DawnduskException
import traceback
#import logging
#logging.basicConfig()

class Dawndusk(XplPlugin):
    '''
    Send Dawn and Dusk messages over XPL
    '''
    def __init__(self):
        """
        Create the dawndusk class
        """
        XplPlugin.__init__(self, name = 'dawndusk')
        self.log.info("dawndusk.__init__ : Start ...")
        self._config = Query(self.myxpl, self.log)

        self.log.debug("dawndusk.__init__ : Try to get configuration from XPL")
        try:
            longitude = str(self._config.query('dawndusk', 'longitude'))
            latitude = str(self._config.query('dawndusk', 'latitude'))
            if latitude == None:
                latitude = "47.352"
            if longitude == None:
                longitude = "5.043"
            boo = self._config.query('dawndusk', 'cron')
            if boo == None:
                boo = "False"
            use_cron = eval(boo)
            boo = self._config.query('dawndusk', 'test')
            if boo == None:
                boo = "False"
            test = eval(boo)
            self.devices = {}
            num = 1
            loop = True
            while loop == True:
                xpltype = self._config.query('dawndusk', \
                    'xpltype-%s' % str(num))
                schema = self._config.query('dawndusk', \
                    'schema-%s' % str(num))
                addname = self._config.query('dawndusk', \
                    'addname-%s' % str(num))
                add = self._config.query('dawndusk', 'add-%s' % str(num))
                command = self._config.query('dawndusk', \
                    'command-%s' % str(num))
                dawn = self._config.query('dawndusk', 'dawn-%s' % str(num))
                dusk = self._config.query('dawndusk', 'dusk-%s' % str(num))
                dawnseconds = self._config.query('dawndusk', 'dawnseconds-%s' % str(num))
                duskseconds = self._config.query('dawndusk', 'duskseconds-%s' % str(num))
                
                if schema != None:
                    self.log.debug("dawndusk.__init__ : Device from \
                        xpl : device=%s," % (add))
                    self.devices[add] = {"schema":schema, "command":command,
                                "dawn":dawn,"dusk":dusk, "dawnseconds":dawnseconds,"duskseconds":duskseconds,
                                "addname":addname, "xpltype":xpltype}
                else:
                    loop = False
                num += 1

        except:
            error = "Can't get configuration from XPL : %s" %  \
                     (traceback.format_exc())
            self.log.error("dawndusk.__init__ : "+error)
            longitude = "5.043"
            latitude = "47.352"
            use_cron = False
            test = False
            raise DawnduskException(error)

        self.log.debug("dawndusk.__init__ : Try to start the dawndusk librairy")
        try:
            self._mydawndusk = DawnduskAPI(longitude, latitude, use_cron, \
                self.myxpl, self.log)
        except:
            error = "Something went wrong during dawnduskAPI init : %s" %  \
                     (traceback.format_exc())
            self.log.error("dawndusk.__init__ : "+error)
            raise DawnduskException(error)

        self.log.debug("dawndusk.__init__ : Try to add the next event \
            to the scheduler")
        try:
            for device in self.devices:
                self.add_next_event(device)

            #for test only
            if test == True :
                self._mydawndusk.sched_add(datetime.datetime.today() + \
                    datetime.timedelta(minutes=1), \
                    self.send_dawndusk,"dawn-test")
                self._mydawndusk.sched_add(datetime.datetime.today() + \
                    datetime.timedelta(minutes=6), \
                        self.send_dawndusk,"dusk-test")
        except:
            error = "Something went wrong during dawnduskScheduler \
                init : %s" %  (traceback.format_exc())
            self.log.error("dawndusk.__init__ : "+error)
            raise DawnduskException(error)

        self.log.debug("dawndusk.__init__ : Try to create listeners")
        Listener(self.dawndusk_cmnd_cb, self.myxpl,
                 {'schema': 'dawndusk.request', 'xpltype': 'xpl-cmnd'})
        if use_cron == True:
            #We need to catch the dawndusk trig message to schedule the next one
            Listener(self.dawndusk_trig_cb, self.myxpl,
                 {'schema': 'dawndusk.basic', 'xpltype': 'xpl-trig'})
        self.enable_hbeat()
        self.log.info("dawndusk plugin correctly started")

    def __del__(self):
        """
        Kill the dawndusk plugin
        """
        del(self._mydawndusk)

    # Todo: add device parameters
    def dawndusk_trig_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self.log.debug("dawndusk.dawndusk_trig_cb() : Start ...")
        mtype = None
        if 'type' in message.data:
            mtype = message.data['type']
        status = None
        if 'status' in message.data:
            status = message.data['status']
        self.log.debug("dawndusk.dawndusk_trig_cb :  type %s received \
            with status %s" % (mtype, status))
        if mtype == "dawndusk" and status != None:
            #We receive a trig indicating that the dawn or dusk has occured.
            #We need to schedule the next one
            self.add_next_event(device)
            for dev in self.devices:
                self.log.debug("sendMessages() : Send message to device %s"%dev)
                mess = XplMessage()
                mess.set_type(self.devices[dev]["xpltype"])
                mess.set_schema(self.devices[dev]["schema"])
                mess.add_data({self.devices[dev]["command"] : \
                    self.devices[dev][status]})
                mess.add_data({self.devices[dev]["addname"] : dev})

                self.myxpl.send(mess)
        self.log.debug("dawndusk.dawndusk_trig_cb() : Done :)")

    def dawndusk_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self.log.debug("dawndusk.dawndusk_cmnd_cb() : Start ...")
        cmd = None
        if 'command' in message.data:
            cmd = message.data['command']
        query = None
        if 'query' in message.data:
            query = message.data['query']
        self.log.debug("dawndusk.dawndusk_cmnd_cb :  command %s received \
            with query %s" % (cmd, query))
        mess = XplMessage()
        mess.set_type("xpl-stat")
        sendit = False
        if cmd == 'status':
            if query == "dawn":
                mess.set_schema("datetime.basic")
                dawn = self._mydawndusk.get_next_dawn()
                mess.add_data({"status": dawn.strftime("%Y%m%d%H%M%S"), \
                    "type": "dawn" })
                sendit = True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, \
                    status= %s" % (query, dawn))
            elif query == "dusk":
                mess.set_schema("datetime.basic")
                dusk = self._mydawndusk.get_next_dusk()
                mess.add_data({"status" :  dusk.strftime("%Y%m%d%H%M%S"), \
                    "type": "dusk" })
                sendit = True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, \
                    satus= %s" % (query, dusk))
            elif query == "fullmoon":
                mess.set_schema("datetime.basic")
                dusk = self._mydawndusk.get_next_fullmoon()
                mess.add_data({"status" :  dusk.strftime("%Y%m%d%H%M%S"), \
                    "type": "fullmoon" })
                sendit = True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, \
                    satus= %s" % (query, dusk))
            if query == "fullmoondawn":
                mess.set_schema("datetime.basic")
                fullmoondawn = self._mydawndusk.get_next_fullmoon_dawn()
                mess.add_data({"status": \
                    fullmoondawn.strftime("%Y%m%d%H%M%S"), \
                    "type": "fullmoondawn" })
                sendit = True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, \
                    status= %s" % (query, fullmoondawn))
            elif query == "fullmoondusk":
                mess.set_schema("datetime.basic")
                fullmoondusk = self._mydawndusk.get_next_fullmoon_dusk()
                mess.add_data({"status" :  \
                    fullmoondusk.strftime("%Y%m%d%H%M%S"), \
                    "type": "fullmoondusk" })
                sendit = True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, \
                    satus= %s" % (query, fullmoondusk))
            elif query == "daynight":
                dawn = self._mydawndusk.get_next_dawn()
                dusk = self._mydawndusk.get_next_dusk()
                mess.set_schema("dawndusk.basic")
                mess.add_data({"type" : "daynight"})
                if dusk < dawn:
                    mess.add_data({"status" :  "day"})
                    self.log.debug("dawndusk.dawndusk_cmnd_cb() : \
                        status= day")
                else :
                    mess.add_data({"status" :  "night"})
                    self.log.debug("dawndusk.dawndusk_cmnd_cb() : \
                        status= night")
                sendit = True
        if sendit:
            self.myxpl.send(mess)
        self.log.debug("dawndusk.dawndusk_cmnd_cb() : Done :)")

    def add_next_event(self,dev):
        """
        Get the next event date : dawn or dusk
        """
        ddate, dstate = self.get_next_event(dev)
        
        if ddate > datetime.datetime.today():
            self._mydawndusk.sched_add(dev,ddate, self.send_dawndusk,dstate)


    def get_next_event(self,device):
        """
        Get the next event date : dawn or dusk
        @return rdate : the next event date
        @return rstate : the event type : DAWN or DUSK
        """
        dawnseconds = 0
        duskseconds = 0
        
        # Get seconds parameters
        if self.devices[device].has_key("dawnseconds") and self.devices[device]["dawnseconds"]!=None:
            dawnseconds = int(self.devices[device]["dawnseconds"])
        if self.devices[device].has_key("duskseconds") and self.devices[device]["duskseconds"]!=None:
            duskseconds = int(self.devices[device]["duskseconds"])
        
        dawn = self._mydawndusk.get_next_dawn()
        dusk = self._mydawndusk.get_next_dusk()
        
        # Add or reduce the n seconds before event
        dawn = dawn + datetime.timedelta(seconds=dawnseconds)
        dusk = dusk + datetime.timedelta(seconds=duskseconds)
        
        self.log.debug("get_next_event for device %s => DAWN = %s" % (device,dawn))
        self.log.debug("get_next_event for device %s => DUSK = %s" % (device,dusk))
        if dusk < dawn :
            rdate = dusk
            rstate = "dusk"
        else :
            rdate = dawn
            rstate = "dawn"
        return rdate, rstate


    def send_dawndusk(self, dev, state):
        """
        Send a xPL message of the type DAWNDUSK.BASIC when the sun goes down or up.
        This function is called by the internal cron
        @param state : DAWN or DUSK
        """
        self.log.debug("dawndusk.sendDawnDusk() for device %s : Start ..." % dev)
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("dawndusk.basic")
        mess.add_data({"type" : "dawndusk"})
        mess.add_data({"status" :  state})
        self.myxpl.send(mess)
        
        self.add_next_event(dev)
        
        # Send XPL Message
        self.log.debug("sendMessages() : Send message to device %s"%dev)
        mess = XplMessage()
        mess.set_type(self.devices[dev]["xpltype"])
        mess.set_schema(self.devices[dev]["schema"])
        mess.add_data({self.devices[dev]["command"] : \
            self.devices[dev][state]})
        mess.add_data({self.devices[dev]["addname"] : dev})
        self.myxpl.send(mess)

        self.log.info("dawndusk : send signal for %s"%state)
        self.log.debug("dawndusk.sendDawnDusk() : Done :-)")


if __name__ == "__main__":
    Dawndusk()