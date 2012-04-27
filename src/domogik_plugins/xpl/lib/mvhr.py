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

Manage mvhr

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
#from domogik.xpl.lib.cron_query import CronQuery
import datetime
from domogik.xpl.common.xplconnector import XplTimer
import threading
import traceback

class HvacMvhr():
    """
    HVACMvhr
    """

    def __init__(self, plugin):
        """
        Init the library
        """
        self.config = plugin.config
        self.log = plugin.log
        self.myxpl = plugin.myxpl
        self._init_lib()

    def __init__(self, config, log, myxpl):
        """
        Init the library
        """
        self.config = config
        self.log = log
        self.myxpl = myxpl
        self._init_lib()

    def _init_lib(self):
        self.log.debug("hvacMvhr.__init__ : Start")
        self.sensors = dict()
        self.mvhr_name = "mvhr1"
        self.sensors_timeout = 10
        self.delay = 5
        self.mvhr_indoor = "S1"
        self.mvhr_outdoor = "S2"
        self.mvhr_insufflation = "S3"
        self.mvhr_reject = ""
        self.mvhr_power = ""
        self.ect = False
        self.ect_tube = ""
        self.ect_outdoor = ""
        self.timer = None
        #self._cronquery = CronQuery(self.myxpl, self.log)

    def reload_config(self):
        """
        Reload the plugin config.
        """
        self.log.debug("reload_config : Try to get configuration from XPL")
        try:
            del(self.sensors)
            self.sensors = dict()
            self.mvhr_name = self.config.query('mvhr', 'name')
            boo = self.config.query('mvhr', 'timeout')
            if boo == None:
                boo = "0"
            self.sensors_timeout = int(boo)
            boo = self.config.query('mvhr', 'delay')
            if boo == None:
                boo = "0"
            self.delay = int(boo)
            self.mvhr_indoor = self.config.query('mvhr', 'mvhr-indoor')
            if (self.mvhr_indoor != None and len(self.mvhr_indoor) != 0):
                self.sensors[self.mvhr_indoor] = {}
            self.mvhr_outdoor = self.config.query('mvhr', 'mvhr-outdoor')
            if (self.mvhr_outdoor != None and len(self.mvhr_outdoor) != 0):
                self.sensors[self.mvhr_outdoor] = {}
            self.mvhr_insufflation = \
                self.config.query('mvhr', 'mvhr-insuffl')
            if (self.mvhr_insufflation != None \
                and len(self.mvhr_insufflation) != 0):
                self.sensors[self.mvhr_insufflation] = {}
            self.mvhr_reject = self.config.query('mvhr', 'mvhr-reject')
            if (self.mvhr_reject != None and len(self.mvhr_reject) != 0):
                self.sensors[self.mvhr_reject] = {}
            self.mvhr_power = self.config.query('mvhr', 'mvhr-power')
            if (self.mvhr_power != None and len(self.mvhr_power) !=0 ):
                self.sensors[self.mvhr_power] = {}
            boo = self.config.query('mvhr', 'ect')
            if boo == None:
                boo = "False"
            self.ect = eval(boo)
            if (self.ect == True):
                self.ect_tube = self.config.query('mvhr', 'ect-tube')
                if (self.ect_tube != None and len(self.ect_tube) != 0):
                    self.sensors[self.ect_tube] = {}
                self.ect_outdoor = self.config.query('mvhr', 'ect-outdoor')
                if (self.ect_outdoor != None and len(self.ect_outdoor) != 0):
                    self.sensors[self.ect_outdoor] = {}
            if self.timer != None:
                self.timer.stop()
            self.timer = XplTimer(self.delay * 60, self.mvhr_xpl_cb, self.myxpl)
            self.timer.start()
            #if self._cronquery.status_job(self.mvhr_name, extkey = "current") \
            #    != "halted":
            #    self._cronquery.halt_job(self.mvhr_name)
            #    self.log.debug("Halt old cron device %s" % self.mvhr_name)
            #nstmess = XplMessage()
            #nstmess.set_type("xpl-trig")
            #nstmess.set_schema("mvhr.basic")
            #nstmess.add_data({"mvhr" : self.mvhr_name})
            #nstmess.add_data({"type" : "cron"})
            #if self._cronquery.start_timer_job(self.mvhr_name, nstmess, \
            #    self.delay * 60):
            #    self.log.debug("Cron device %s activated" % self.mvhr_name)
            #else:
            #    self.log.error("Can't activate cron device %s" % \
            #        self.mvhr_name)
            self.log.debug("hvacMvhr.__init__ : sensors : %s " % self.sensors)
        except:
            error = "Can't get configuration from XPL : %s" %  \
                     (traceback.format_exc())
            self.log.exception("mvhr.reload_config : " + error)
            return False
        self.log.debug("hvacMvhr.reloadconfig : Done")
        return True

#    def leave(self):
#        """
#        Stop the library
#        """
#        self._cronquery.halt_job(self.mvhr_name)


    def sensor_current(self, sensor):
        """
        Return the current value of a sensor
        """
        if (sensor in self.sensors
            and "current" in self.sensors[sensor]):
            return self.sensors[sensor]["current"]
        else:
            return "not-found"

    def exchanger_efficiency(self):
        """
        Return efficiency of the mvhr
        """
        if (self.mvhr_outdoor in self.sensors
            and self.mvhr_indoor in self.sensors
            and self.mvhr_insufflation in self.sensors
            and "current" in self.sensors[self.mvhr_indoor]
            and "current" in self.sensors[self.mvhr_outdoor]
            and "current" in self.sensors[self.mvhr_insufflation]):
            res = ((self.sensors[self.mvhr_insufflation]["current"] - \
                self.sensors[self.mvhr_outdoor]["current"]) / \
                (self.sensors[self.mvhr_indoor]["current"] - \
                self.sensors[self.mvhr_outdoor]["current"])) * 100
            return "%.2f" % res
        else:
            return "not-found"

    def helper_status(self, params={}):
        """
        Return status of a device
        """
        self.log.debug("helper_status : Start ...")
        data = []
        data.append("Exchanger efficiency : %s" % \
            self.exchanger_efficiency())
        data.append("Outdoor temperature : %s" % \
            self.sensor_current(self.mvhr_outdoor))
        data.append("Indoor temperature : %s" % \
            self.sensor_current(self.mvhr_indoor))
        data.append("Insufflation temperature : %s" % \
            self.sensor_current(self.mvhr_insufflation))
        self.log.debug("helper_status : Done")
        return data

    def helper_reload_config(self, params={}):
        """
        Reload config of the plugin
        """
        self.log.debug("helper_reload_config : Start ...")
        data = []
        res = self.reload_config()
        data.append("Reload config of the plugin : %s" % res)
        return data

    def req_gate_info(self, myxpl, message):
        """
        Requests the sending of an mvhr.gateinfo message containing
        details of the xPL connector software.
        @param myxpl : The XPL sender
        @param message : The XPL message

        mvhr.request
        {
         request=gateinfo
        }

        mvhr.gateinfo
        {
         protocol=[X10|UPB|CBUS|ZWAVE|INSTEON]
         description=
         version=
         author=
         info-url=
         zone-count=#
        }
        """
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("mvhr.gateinfo")
        mess.add_data({"protocol" : "MVHR"})
        mess.add_data({"description" : "Manage an mvhr with xpl"})
        mess.add_data({"version" :  "0.1"})
        mess.add_data({"author" : "Domogik Team"})
        mess.add_data({"info-url" : "http://wiki.domogik.org/plugin_hvac_mvhr"})
        mess.add_data({"request-list" : "mvhrinfo,mvhr"})
        mess.add_data({"command-list" : "none"})
        mess.add_data({"device-list" : self.mvhr_name})
        myxpl.send(mess)

    def req_mvhr_info(self, myxpl, message):
        """
        This schema reports the configuration of a mvhr, the modes
        that can be set and the states that it can report. It is
        sent as an xPL status message in response to an
        mvhr.request with request=mvhrinfo.
        @param myxpl : The XPL sender
        @param message : The XPL message

        mvhr.request
        {
         request=mvhrinfo
         mvhr=id
        }

        mvhr.mvhrinfo
        {
         mvhr=id
         mvhr-mode-list=
         ect-mode-list=
         fan-mode-list=
         mvhr-state-list=
         ect-state-list=
         fan-state-list=
         }
        """
        mvhr = None
        if 'mvhr' in message.data:
            mvhr = message.data['mvhr']
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("mvhr.mvhrinfo")
        if mvhr == None:
            mess.add_data({"error" : "Missing parameter : mvhr"})
            self.log.error("request = %s : Missing parameter _ mvhr _." \
                % ("mvhrinfo"))
        elif mvhr != self.mvhr_name:
            mess.add_data({"error" : "mvhr not found : %s" % mvhr})
            self.log.error("request = %s : MVHR _ %s _ not found." % \
                ("mvhrinfo", mvhr))
        else:
            mess.add_data({"mvhr" : mvhr})
            mess.add_data({"ect-mode-list" : "on,off"})
            mess.add_data({"mvhr-mode-list" : "heat,bypass,cool"})
            mess.add_data({"fan-mode-list" : "on,off,auto"})
            mess.add_data({"ect-state-list" : "on,off"})
            mess.add_data({"mvhr-state-list" : "heat,bypass,cool"})
            mess.add_data({"fan-state-list" : "on,off"})
        myxpl.send(mess)


    def req_mvhr(self, myxpl, message):
        """
        Requests the sending of an mvhr.mvhr message describing
        the current state of the specified mvhr.
        @param myxpl : The XPL sender
        @param message : The XPL message

        mvhr.request
        {
         request=mvhr
         mvhr=id
        }

        mvhr.mvhr
        {
         mvhr=id
        }
        """
        mvhr = None
        if 'mvhr' in message.data:
            mvhr = message.data['mvhr']
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("mvhr.mvhr")
        if mvhr == None:
            self.log.error("Request = %s : Missing parameter _ mvhr _." % \
                ("mvhr"))
            mess.add_data({"error" : "Missing parameter : mvhr"})
        elif mvhr != self.mvhr_name:
            mess.add_data({"error" : "Mvhr not found : %s" % mvhr})
            self.log.error("Request = %s : Mvhr _ %s _ not found." % \
                ("mvhr", mvhr))
        else:
            mess.add_data({"mvhr" : mvhr})
            self.mvhr_message(mess)
            if self.ect :
                self.ect_message(mess)
        myxpl.send(mess)

    def mvhr_message(self, mess):
        """
        Add the mvhr part to the message
        """
        mess.add_data({"mvhr-mode" : "bypass"})
        mess.add_data({"fan-mode" : "auto"})
        mess.add_data({"mvhr-eff" : 0})
        mess.add_data({"exchng-eff" : self.exchanger_efficiency()})
        mess.add_data({"mvhr-outdoor" : \
            self.sensor_current(self.mvhr_outdoor)})
        mess.add_data({"mvhr-indoor" : \
            self.sensor_current(self.mvhr_indoor)})
        mess.add_data({"mvhr-insuffl" : \
            self.sensor_current(self.mvhr_insufflation)})

    def ect_message(self, mess):
        """
        Add the ect part to the message
        """
        res = 0
        mess.add_data({"ect-mode" : "off"})
        mess.add_data({"ect-eff" : 0})
        if (self.ect_outdoor in self.sensors
            and self.ect_tube in self.sensors
            and "current" in self.sensors[self.ect_tube]
            and "current" in self.sensors[self.ect_outdoor]):
            res = self.sensors[self.ect_tube]["current"] - \
                self.sensors[self.ect_outdoor]["current"]
            mess.add_data({"ect-delta" : res})
        if (self.ect_outdoor in self.sensors
            and "current" in self.sensors[self.ect_outdoor]):
            mess.add_data({"ect-outdoor" : \
                self.sensors[self.ect_outdoor]["current"]})
        if (self.ect_tube in self.sensors
            and "current" in self.sensors[self.ect_tube]):
            mess.add_data({"ect-tube" : \
                self.sensors[self.ect_tube]["current"]})

    def sensor_trig_listener(self, myxpl, message):
        """
        Listen to the trig messages of the sensors
        """
        device = None
        if 'device' in message.data:
            device = message.data['device']
        self.log.debug("hvacMvhr.sensor_trig_listener : value from \
device %s received" % (device))
        if (device in self.sensors):
            current = 0
            if 'current' in message.data:
                current = message.data['current']
                self.log.debug("hvacMvhr.sensor_trig_listener : add \
value %s to sensors" % (current))
                self.sensors[device]["current"] = float(current)
                self.sensors[device]["last"] = datetime.datetime.today()

#    def mvhr_trig_listener(self, myxpl, message):
#        """
#        List to the mvhr messages
#        """
#        mvhr = None
#        if 'mvhr' in message.data:
#            mvhr = message.data['mvhr']
#        mtype = None
#        if 'type' in message.data:
#            mtype = message.data['type']
#        self.log.debug("hvacMvhr.mvhr_trig_listener : message for \
#mvhr %s (%s) received" % (mvhr, mtype))
#        if (mvhr == self.mvhr_name and mtype == "cron"):
#            mess = XplMessage()
#            mess.set_type("xpl-trig")
#            mess.set_schema("mvhr.basic")
#            mess.add_data({"mvhr" : mvhr})
#            self.mvhr_message(mess)
#            if self.ect :
#                self.ect_message(mess)
#            myxpl.send(mess)

    def mvhr_xpl_cb(self):
        """
        Callback function of the xpltimer
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("mvhr.basic")
        mess.add_data({"mvhr" : self.mvhr_name})
        self.mvhr_message(mess)
        if self.ect :
            self.ect_message(mess)
        self.myxpl.send(mess)

    def request_listener(self, myxpl, message):
        """
        Listen to mvhr.request messages
        @param message : The XPL message
        @param myxpl : The XPL sender

        mvhr.request
        {
         request=gateinfo|zonelist|zoneinfo|zone|setpoint|timer|runtime|fantime
         zone=id
         [setpoint=]
         [state=]
        }
        """
        self.log.debug("hvacMvhr.request_listener : Start ...")
        requests = {
            'gateinfo': lambda x,m: self.req_gate_info(x,m),
            'mvhrinfo': lambda x,m: self.req_mvhr_info(x,m),
            'mvhr': lambda x,m: self.req_mvhr(x,m),
        }
        request = None
        if 'request' in message.data:
            request = message.data['request']
        self.log.debug("hvacMvhr.request_listener : request %s \
            received" % (request))
        try:
            requests[request](myxpl, message)
        except:
            self.log.error("Request _ %s _ unknown." % (request))
            error = "Exception : %s" % (traceback.format_exc())
            self.log.debug("hvacMvhr.request_listener : " + error)

if __name__ == "__main__":
    MVHR = HvacMvhr()
