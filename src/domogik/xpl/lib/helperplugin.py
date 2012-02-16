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
Extends the XplPlugin to add a helper

Implements
==========
class pluginHelper
class XplHlpPlugin(XplPlugin)
    def enable_helper(self)

Helps
=====
Developpers who wants to use it must declare a dict() like this in the
init of the plugin and enable the helper just before the heartbeat

    def __init__(self):

        ...

        self.helpers =   \
           { "list" :
              {
                "cb" : self.helperList,
                "desc" : "List devices (cron jobs)",
                "usage" : "list all (all the devices)|aps(jobs in APScheduler)",
                "param-list" : "which",
                "which" : "all|aps",
              },
             "info" :
              {
                "cb" : self.helperInfo,
                "desc" : "Display device information",
                "usage" : "info <device>",
                "param-list" : "device",
                "device" : "<device>",
              },
            }

        ...

        self.enable_helper()
        self.enable_hbeat()

A simple helper looks like this

    def helperInfo(self, params={}):
        data = []
        if "device" in params:
            device=params["device"]
            # What you want to do
            data.append("What you want to return to the screen")
        else:
            data.append("No ""device"" parameter found")
        return data

How to use it :

Ask the capabilties of the gateinfo
helper.request
{
request=gateinfo
}
The helper plugin will respond:
helper.gateinfo
{
status=ok
name=cron
cmnd-list=info,stop,list,halt,resume
}

Now you can ask the details of each commands in cmnd-list :
helper.request
{
request=cmndinfo
plugin=cron
command=list
}
The helper plugin will respond:
helper.cmndinfo
{
plugin=cron
command=list
param-list=which
which=all|aps
status=ok
}

Now, you've got everything to call the function in the helper plugin :
helper.basic
{
plugin=cron
command=list
which=all
}
The helper plugin will respond:
helper.basic
{
plugin=cron
command=list
screen1=List all devices :
screen2=device     | status   |    #runs |     #aps | uptime(in s)
screen3=wakeup     | started  |        0 |        7 |    41.170483
screen4=garden     | started  |        0 |       28 |    40.940044
screen5=wakedawn   | started  |        0 |       63 |    40.701335
screen-count=5
status=ok
}

Look at the cron plugin to see a full example :
bin/cron.py to see the helpers declaration
lib/cron.py to see the helpers functions

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
import traceback

class pluginHelper():
    def __init__(self,parent):
        """
        """
        self._parent=parent
        self._params=["usage","desc","param-list"]

    def isActive(self):
        """
        """
        try:
            titi=self._parent.helpers
            return True
        except:
            return False
        return True

    def cmndName(self,callback):
        """
        """
        return str(callback)

    def isValidCmnd(self,command):
        """
        """
        return command!=None and command in self._parent.helpers

#    def registerAll(self):
#        """
#        deprecated
#        """
#        params=["help","param-list"]
#
#    def register(self,command,callback,conf):
#        """
#        deprecated
#        """
#        params=["usage","desc","param-list"]
#        if self.isValidCmnd(command):
#            return False
#        else:
#            self._cmnds[command]={"cb" : lambda p : callback}
#            for p in params:
#                self._cmnds[command][p]=conf[p]
#            for p2 in self._cmnds[command]["param-list"].split(","):
#                self._cmnds[command][p2]=conf[p2]
#        return True
#
#    def fragment(self,value):
#        """
#        Fragment a value to a size beetween 100 an 128
#        """
#        res=list()
#        while len(value)>128:
#            idxc=value.rfind(",",0,127)
#            res.append(value[0:idxc])
#            value=value[idxc+1:]
#        res.append(value)
#        return res

    def status(self):
        """
        """
        if self.isActive():
            return "ok"
        else :
            return "not-found"

    def reqGateinfo(self,myxpl,message,request):
        """
        """
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("helper.gateinfo")
        mess.add_data({"status" : self.status()})
        mess.add_data({"plugin" : self._parent._name})
        if self.isActive():
            l=""
            for cmnd in self._parent.helpers:
                if l=="":
                    l=cmnd
                else:
                    l=l+","+cmnd
            if l!="":
                mess.add_data({"cmnd-list" : l})
        myxpl.send(mess)

    def reqCmndinfo(self,myxpl,message,request):
        """
        """
        plugin=None
        if 'plugin' in message.data:
            plugin = message.data['plugin']
        if plugin!=self._parent._name:
            return False
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("helper.cmndinfo")
        mess.add_data({"plugin" : self._parent._name})
        try:
            cmnd = None
            if 'command' in message.data:
                    cmnd = message.data['command']
            if not self.isValidCmnd(cmnd):
                mess.add_data({"command" : cmnd})
                mess.add_data({"status" : "not-found"})
            else:
                mess.add_data({"command" : cmnd})
                if self._parent.helpers[cmnd]["param-list"]!="":
                    mess.add_data({"param-list" : self._parent.helpers[cmnd]["param-list"]})
                for p in self._parent.helpers[cmnd]["param-list"].split(","):
                    mess.add_data({p : self._parent.helpers[cmnd][p]})
                mess.add_data({"status" : "ok"})
        except:
            mess.add_data({"status" : "error"})
            self._parent.log.error(""+traceback.format_exc())
        myxpl.send(mess)

    def requestCmndListener(self,message):
        """
        Listen to plugin.request messages
        @param message : The XPL message
        @param myxpl : The XPL sender
        """
        requests = {
            'gateinfo': lambda x,m,r: self.reqGateinfo(x,m,r),
            'cmndinfo': lambda x,m,r: self.reqCmndinfo(x,m,r),
        }
        try:
            request = None
            if 'request' in message.data:
                request = message.data['request']
            self._parent.log.debug("pluginHelper.requestDeviceListener : request %s received" % (request))
            requests[request](self._parent.myxpl,message,request)
        except:
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self._parent.log.error("pluginHelper.requestDeviceListener : "+error)

    def basicCmndListener(self,message):
        """
        """
        self._parent.log.debug("pluginHelper.basicDeviceListener : Start ...")
        plugin = None
        if 'plugin' in message.data:
            plugin = message.data['plugin']
        if plugin!=self._parent._name:
            return False
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("helper.basic")
        mess.add_data({"plugin" : self._parent._name})
        try:
            command = None
            if 'command' in message.data:
                command = message.data['command']
            mess.add_data({"command" : command})
            self._parent.log.debug("pluginHelper : command %s received" % (command))
            if command!=None:
                params={}
                if self.isValidCmnd(command):
                    for p in self._parent.helpers[command]["param-list"].split(","):
                        if p in message.data:
                            params[p]=message.data[p]
                    ret=self._parent.helpers[command]["cb"](params)
                    i=1
                    for l in ret:
                        mess.add_data({"screen%s"%i : l})
                        i=i+1
                    mess.add_data({"screen-count" : i-1})
                    mess.add_data({"status" : "ok"})
                else:
                    mess.add_data({"status" : "not-found"})
            else:
                mess.add_data({"status" : "not-found"})
        except:
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self._parent.log.error("pluginHelper.basicDeviceListener : "+error)
            mess.add_data({"status" : "error"})
        self._parent.myxpl.send(mess)

class XplHlpPlugin(XplPlugin):
    def __init__(self, name, stop_cb = None, is_manager = False, reload_cb = None, dump_cb = None, parser = None,
                 daemonize = True):
        """
        Create the telldus class
        This class is used to connect devices (through telldus) to the xPL Network
        """
        XplPlugin.__init__(self, name, stop_cb, is_manager, reload_cb, dump_cb, parser, daemonize)
        self._helper=pluginHelper(self)
        #Create listeners
        print "active=%s"%self._helper.isActive()

    def enable_helper(self):
        print "active=%s"%self._helper.isActive()
        if self._helper.isActive():
            Listener(self._helper.requestCmndListener, self.myxpl,
                    {'schema': 'helper.request', 'xpltype': 'xpl-cmnd'})
            Listener(self._helper.basicCmndListener, self.myxpl,
                    {'schema': 'helper.basic', 'xpltype': 'xpl-cmnd'})


if __name__ == "__main__":
    XplHlpPlugin()
