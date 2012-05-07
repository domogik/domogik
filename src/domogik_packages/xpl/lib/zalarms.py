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
Program alarms to the cron plugin.

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import datetime
import math
from domogik.xpl.common.xplmessage import XplMessage
import traceback
from domogik.xpl.lib.cron_query import CronQuery

class zalarmsAPI:
    """
    cron API
    """

    def __init__(self,config,myxpl,log):
        """
        Constructor
        @param plugin : the parent plugin (used to retrieve)
        """
        self.log=log
        self.myxpl=myxpl
        self.config=config
        self._cron_query = CronQuery(self.myxpl,self.log)
        self._devices=set()

        if self.config!=None :
            num = 1
            loop = True
            while loop == True:
                device = self.config.query('zalarms', 'device-%s' % str(num))
                if device!=None:
                    self._devices.add(device)
                    #print "status=%s"%self._cron_query.statusJob(device,extkey="current")
                    alarmtype = self.config.query('zalarms', 'alarmtype-%s' % str(num))
                    if self._cron_query.status_job(device,extkey="current")!="halted":
                        self._cron_query.halt_job(device)
                    alarms=list()
                    alarm1 = self.config.query('zalarms', 'alarm1-%s' % str(num))
                    if alarm1!=None:
                        alarms.append(alarm1)
                    alarm2 = self.config.query('zalarms', 'alarm2-%s' % str(num))
                    if alarm2!=None:
                        alarms.append(alarm2)
                    alarm3 = self.config.query('zalarms', 'alarm3-%s' % str(num))
                    if alarm3!=None:
                        alarms.append(alarm3)
                    nstschema = self.config.query('zalarms', 'nstschema-%s' % str(num))
                    nsttype = self.config.query('zalarms', 'nsttype-%s' % str(num))
                    parameter1 = self.config.query('zalarms', 'parameter1-%s' % str(num))
                    valueon1 = self.config.query('zalarms', 'valueon1-%s' % str(num))
                    valueoff1 = self.config.query('zalarms', 'valueoff1-%s' % str(num))
                    parameter0 = self.config.query('zalarms', 'parameter0-%s' % str(num))
                    valueon0 = self.config.query('zalarms', 'valueon0-%s' % str(num))
                    valueoff0 = self.config.query('zalarms', 'valueoff0-%s' % str(num))
                    nstfield1 = self.config.query('zalarms', 'nstfield1-%s' % str(num))
                    nstvalue1 = self.config.query('zalarms', 'nstvalue1-%s' % str(num))
                    nstfield2 = self.config.query('zalarms', 'nstfield2-%s' % str(num))
                    nstvalue2 = self.config.query('zalarms', 'nstvalue2-%s' % str(num))
                    nstfield3 = self.config.query('zalarms', 'nstfield3-%s' % str(num))
                    nstvalue3 = self.config.query('zalarms', 'nstvalue3-%s' % str(num))
                    nstMess = XplMessage()
                    nstMess.set_type(nsttype)
                    nstMess.set_schema(nstschema)
                    params={}
                    if parameter0!=None:
                        params[parameter0]={"valueon":valueon0,"valueoff":valueoff0}
                    if parameter1!=None:
                        params[parameter1]={"valueon":valueon1,"valueoff":valueoff1}
                    if nstfield1!=None:
                        nstMess.add_data({nstfield1 : nstvalue1})
                    if nstfield2!=None:
                        nstMess.add_data({nstfield2 : nstvalue2})
                    if nstfield3!=None:
                        nstMess.add_data({nstfield3 : nstvalue3})
                    if alarmtype=="alarm":
                        self._cron_query.start_alarm_job(device, nstMess,
                            params=params, alarms=alarms)
                    else :
                        self._cron_query.start_dawn_alarm_job(device,nstMess,params=params,alarms=alarms)
                else:
                    loop = False
                num += 1

    def __del__(self):
        """

        """
        #for dev in self._devices:
        #    self._cron_query.haltJob(dev)

    def requestListener(self,message):
        """
        Listen to timer.request messages
        @param message : The XPL message
        @param myxpl : The XPL sender

        timer.request
            {
             device=<name of the timer>
            }
        timer.basic
            {
             device=<name of the timer>
             type=timer|date|interval|cron
             current=halted|resumed|stopped|started
             elapsed=<number of seconds since device created>
             runtime=<number of seconds since device in started state>
             runtimes=<number of messages sent>
            }
        """
        try:
            self.log.debug("zalarms.requestListener : Start ...")
            #device = None
            #if 'device' in message.data:
            #    device = message.data['device']
            #mess = XplMessage()
            #mess.set_type("xpl-stat")
            #mess.set_schema("timer.basic")
            #mess.add_data({"device" : device})
            #if device in self.jobs.data.iterkeys():
            #    mess.add_data({"type" : self.jobs.data[device]['devicetype']})
            #    mess.add_data({"current" : self.jobs.data[device]['current']})
            #    mess.add_data({"elapsed" : self.jobs.getUpTime(device)})
            #    mess.add_data({"runtime" : self.jobs.getRunTime(device)})
#                mess.add_data({"uptime" : self.jobs.getUpTime(device)})
            #    mess.add_data({"runtimes" : self.jobs.getRunTimes(device)})
            #else:
            #    mess.add_data({"elasped" :  0})
            #    mess.add_data({"current" : "halted"})
            #self.myxpl.send(mess)
            #self.log.debug("cronAPI.requestListener : Done :)")
        except:
            self.log.error("action _ %s _ unknown."%(request))
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self.log.debug("zalarms.requestListener : "+error)


if __name__ == "__main__":
    dd = zalarmsAPI()
    #l, c = dd.get_dawn_dusk(-01.7075, 48.1173, 1)
    #print(l)
    #print(c)
