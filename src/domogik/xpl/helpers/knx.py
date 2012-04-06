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

Get informations about one wire network

Implements
==========

TODO

@author: Basilic <basilic3@htomail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""



from urllib import *
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.knx import KNXException
from domogik.xpl.lib.knx import KNX
from domogik.common.configloader import *
from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError



class KNXHelper(Helper):
   
   datatype=["1.001","1.008","5.xxx","5.001","5.003","6.xxx","7.xxx","8.xxx","9.xxx","10.001","11.001","12.xxx","13.xxx","14.xxx","16.000","20.102","DT_HVACEib"]
   datatypedesc=["Switch on/off","Blinds controle up/down","8 bit unsigned int","Scaling 0-100%","Angle 0-360","8bit signed int EIS14","16bit unsigned int EIS10","16bit signed int","16bit floating point number EIS5","Time","Date","32bit unsigned int EIS11","32bit signed int","32bit IEEE754 floating point number","String EIS15","HVAC Heating mode (comfort,standby,night,frost)","Special for TB042"]


   def __init__(self):
      print "test"
      self.commands =   \
               { "add" : 
                  {
                    "cb" : self.add,
                    "desc" : "add a devices on knx config file and in database",
                    "usage" : "add"
                  },
               }
#   def all(self, args=None):


   def add(self,args=None):
#      XplPlugin.__init__(self, name ='knx')
#      self._config = Query(self.myxpl, self.log)
#      fichiertoopen=self._config.query('knx','file')
      fichiertoopen="/home/domogik/knx.txt"
      print fichiertoopen

#      datatype=["1.001","1.008","5.xxx","5.001","5.003","6.xxx","7.xxx","8.xxx","9.xxx","10.001","11.001","12.xxx","13.xxx","14.xxx","16.000","20.102","DT_HVACEib"]
#      datatypedesc=["Switch on/off","Blinds controle up/down","8 bit unsigned int","Scaling 0-100%","Angle 0-360","8bit signed int EIS14","16bit unsigned int EIS10","16bit signed int","16bit floating point number EIS5","Time","Date","32bit unsigned int EIS11","32bit signed int","32bit IEEE754 floating point number","String EIS15","HVAC Heating mode (comfort,standby,night,frost)","Special for TB042"]

      usagelist=[]
      typelist=[]
      cfg = Loader('rest')
      config = cfg.load()
      conf = dict(config[1])
      REST_URL= "http://%s:%s" % (conf["rest_server_ip"], conf ["rest_server_port"])

      Name=raw_input("Enter Name of device:")
      Adr_dmg=raw_input('Domogik Address:')

      addresse=REST_URL+"/base/device_type/list"
      page=urlopen(addresse)
      strpage=page.read()

      while strpage.find("knx.")>0:
         strpage=strpage[strpage.find("knx.")+4:]
         typelist.append(strpage[:strpage.find(',')-1])
      for i in range(len(typelist)):
         print "%s - %s" %(i,typelist[i])

      typel=raw_input('Select your device type:')
      typel=int(typel)
      addresse=REST_URL+"/base/device_usage/list/"

      page=urlopen(addresse)
      strpage=page.read()

      while strpage.find("id")>0:
         strpage=strpage[strpage.find("id")+7:]
         usagelist.append(strpage[:strpage.find(',')-1])
      for i in range(len(usagelist)):
         print "%s - %s" %(i,usagelist[i])

      usagel=raw_input('Select your usage: ')
      if usagel<>"":
         usagel=int(usagel)

      Adr_cmd=raw_input('KNX command groups: ')

      for i in range(len(datatype)):
         print "%s - %s - %s" %(i,datatype[i],datatypedesc[i])
      Datatype_cmd=raw_input('Select your Datapoint type: ')
      if Datatype_cmd<>"":
         Datatype_cmd=int(Datatype_cmd)
      else:
         Datatype_cmd=0
  
      Adr_stat=raw_input('KNX listerner groups: ')
      if Adr_stat=="":
         Adr_stat=Adr_cmd
  
      if usagel=="" or typel=="" or Name=="" or Adr_dmg=="":
         print "Error empty value not acceptable for Name, Address, Type or Usage"
      adresse=REST_URL+'/base/device/add/name/'+Name+"/address/"+Adr_dmg+'/type_id/knx.'+typelist[typel]+'/usage_id/'+usagelist[usagel]

      print adresse
      page=urlopen(adresse)
      strpage=page.read()
      print strpage

      filetoopen="/home/domogik/knx.txt" # a mettre dans /src/share/domogik/data
      fichier=open(filetoopen,"a")
      ligne="datatype:%s adr_dmg:%s adr_cmd:%s adr_stat:%s end \n" %(datatype[Datatype_cmd],Adr_dmg,Adr_cmd,Adr_stat)
      print ligne
      fichier.write(ligne)
      fichier.close

MY_CLASS = {"cb": KNXHelper}
