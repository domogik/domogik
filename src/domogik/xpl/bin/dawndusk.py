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
@copyright: (C) 2007-2009 Domogik project
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
from domogik.xpl.lib.dawndusk import dawnduskAPI
from domogik.xpl.lib.dawndusk import dawnduskScheduler
from domogik.xpl.lib.dawndusk import dawnduskException
import traceback
import logging

#logging.basicConfig()

class dawndusk(XplPlugin):
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
            if latitude==None:
                latitude="47.352"
            if longitude==None:
                longitude="5.043"
            boo=self._config.query('dawndusk', 'cron')
            if boo==None:
                boo="False"
            use_cron = eval(boo)
        except:
            error = "Can't get configuration from XPL : %s" %  \
                     (traceback.format_exc())
            self.log.error("dawndusk.__init__ : "+error)
            longitude = "5.043"
            latitude = "47.352"
            use_cron = False
            raise dawnduskException(error)

        self.log.debug("dawndusk.__init__ : Try to start the dawndusk librairy")
        try:
            self._mydawndusk = dawnduskAPI(longitude,latitude,use_cron,self.myxpl,self.log)
        except:
            error = "Something went wrong during dawnduskAPI init : %s" %  \
                     (traceback.format_exc())
            self.log.error("dawndusk.__init__ : "+error)
            raise dawnduskException(error)

        self.log.debug("dawndusk.__init__ : Try to add the next event to the scheduler")
        try:
            self.addNextEvent()
        except:
            error = "Something went wrong during dawnduskScheduler init : %s" %  \
                     (traceback.format_exc())
            self.log.error("dawndusk.__init__ : "+error)
            raise dawnduskException(error)

        self.log.debug("dawndusk.__init__ : Try to create listeners")
        Listener(self.dawndusk_cmnd_cb, self.myxpl,
                 {'schema': 'dawndusk.request', 'xpltype': 'xpl-cmnd'})
        if use_cron==True:
            #We need to catch the dawndusk trig message to schedule the next one
            Listener(self.dawndusk_trig_cb, self.myxpl,
                 {'schema': 'dawndusk.basic', 'xpltype': 'xpl-trig'})
        self.enable_hbeat()
        self.log.info("dawndusk plugin correctly started")

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
        self.log.debug("dawndusk.dawndusk_trig_cb :  type %s received with status %s" %
                       (mtype,status))
        if mtype=="dawndusk" and status!=None:
            #We receive a trig indicating that the dawn or dus has occured.
            #We need to schedule the next one
            self.addNextEvent()
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
        self.log.debug("dawndusk.dawndusk_cmnd_cb :  command %s received with query %s" %
                       (cmd,query))
        mess = XplMessage()
        mess.set_type("xpl-stat")
        sendit=False
        if cmd=='status':
            if query=="dawn":
                mess.set_schema("datetime.basic")
                dawn = self._mydawndusk.getNextDawn()
                mess.add_data({"status": dawn.strftime("%Y%m%d%H%M%S"), "type": "dawn" })
                sendit=True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, status= %s" % (query,dawn))
            elif query=="dusk":
                mess.set_schema("datetime.basic")
                dusk = self._mydawndusk.getNextDusk()
                mess.add_data({"status" :  dusk.strftime("%Y%m%d%H%M%S"), "type": "dusk" })
                sendit=True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, satus= %s" % (query,dusk))
            elif query=="fullmoon":
                mess.set_schema("datetime.basic")
                dusk = self._mydawndusk.getNextFullMoon()
                mess.add_data({"status" :  dusk.strftime("%Y%m%d%H%M%S"), "type": "fullmoon" })
                sendit=True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, satus= %s" % (query,dusk))
            if query=="fullmoondawn":
                mess.set_schema("datetime.basic")
                fullmoondawn = self._mydawndusk.getNextFullMoonDawn()
                mess.add_data({"status": fullmoondawn.strftime("%Y%m%d%H%M%S"), "type": "fullmoondawn" })
                sendit=True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, status= %s" % (query,fullmoondawn))
            elif query=="fullmoondusk":
                mess.set_schema("datetime.basic")
                fullmoondusk = self._mydawndusk.getNextFullMoonDusk()
                mess.add_data({"status" :  fullmoondusk.strftime("%Y%m%d%H%M%S"), "type": "fullmoondusk" })
                sendit=True
                self.log.debug("dawndusk.dawndusk_cmnd_cb :  query= %s, satus= %s" % (query,fullmoondusk))
            elif query=="daynight":
                dawn = self._mydawndusk.getNextDawn()
                dusk = self._mydawndusk.getNextDusk()
                mess.set_schema("dawndusk.basic")
                mess.add_data({"type" : "daynight"})
                if dusk < dawn:
                    mess.add_data({"status" :  "day"})
                    self.log.debug("dawndusk.dawndusk_cmnd_cb() : status= day")
                else :
                    mess.add_data({"status" :  "night"})
                    self.log.debug("dawndusk.dawndusk_cmnd_cb() : status= night")
                sendit=True
        if sendit:
            self.myxpl.send(mess)
        self.log.debug("dawndusk.dawndusk_cmnd_cb() : Done :)")

    def addNextEvent(self):
        """
        Get the next event date : dawn or dusk
        """
        self.log.debug("dawndusk.addNextEvent() : Start ...")
        ddate, dstate = self.getNextEvent()
        #for test only
        #self._mydawndusk.schedAdd(datetime.datetime.today()+datetime.timedelta(seconds=30),self.sendDawnDusk,"dawn")
        #self._mydawndusk.schedAdd(datetime.datetime.today()+datetime.timedelta(seconds=45),self.sendDawnDusk,"dawn")
        self.log.info("Add a new event %s at %s to the scheduler" % (dstate,ddate))
        self._mydawndusk.schedAdd(ddate,self.sendDawnDusk,dstate)
        self.log.debug("dawndusk.addNextEvent() : Done :-)")

    def getNextEvent(self):
        """
        Get the next event date : dawn or dusk
        @return rdate : the next event date
        @return rstate : the event type : DAWN or DUSK
        """
        self.log.debug("dawndusk.getNextEvent() : Start ...")
        dawn = self._mydawndusk.getNextDawn()
        dusk = self._mydawndusk.getNextDusk()
        if dusk < dawn :
            rdate = dusk
            rstate = "dusk"
        else :
            rdate = dawn
            rstate = "dawn"
        self.log.debug("dawndusk.getNextEvent() : Done :-)")
        return rdate,rstate

    def sendDawnDusk(self,state):
        """
        Send a xPL message of the type DAWNDUSK.BASIC when the sun goes down or up
        @param state : DAWN or DUSK
        """
        self.log.debug("dawndusk.sendDawnDusk() : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("dawndusk.basic")
        mess.add_data({"type" : "dawndusk"})
        if state=="dawn":
            mess.add_data({"status" :  "dawn"})
        elif state=="dawn":
            mess.add_data({"status" :  "dusk"})
        self.myxpl.send(mess)
        self.addNextEvent()
        self.log.info("dawndusk : send signal for %"%state)
        self.log.debug("dawndusk.sendDawnDusk() : Done :-)")

if __name__ == "__main__":
    dawndusk()
