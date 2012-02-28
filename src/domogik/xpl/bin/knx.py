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

KNX bus

Implements
==========

- KnxManager

@author: Fritz <fritz.smh@gmail.com> Basilic <Basilic3@hotmail.com>...
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.knx import KNXException
from domogik.xpl.lib.knx import KNX
import threading
import subprocess
import time

listknx=["debut","fin"]

class KNXManager(XplPlugin):
    """ Implements a listener for KNX command messages 
        and launch background listening for KNX events
    """

    def __init__(self):
        """ Create listener and launch bg listening
        """
        XplPlugin.__init__(self, name = 'knx')

        # Configuration : KNX device
        self._config = Query(self.myxpl, self.log)
        device = self._config.query('knx', 'device')

        ### Create KNX object
        try:
            self.knx = KNX(self.log, self.send_xpl)
            self.log.info("Open KNX for device : %s" % device)
            self.knx.open(device)

        except KNXException as err:
            self.log.error(err.value)
            print(err.value)
            self.force_leave()
            return

        ### Start listening 
        try:
            self.log.info("Start listening to KNX")
            knx_listen = threading.Thread(None,
                                          self.knx.listen,
                                          "listen_knx",
                                          (),
                                          {})
            knx_listen.start()
        except KNXException as err:
            self.log.error(err.value)
            print(err.value)
            self.force_leave()
            return


        ### Create listeners for commands
        self.log.info("Creating listener for KNX")
        Listener(self.knx_cmd, self.myxpl,{'schema':'knx.basic'})
        self.add_stop_cb(self.knx.close)
        self.enable_hbeat()

        ### Load the configuration file in the plugin
        filetoopen=self._config.query('knx','file')
        fichier=open(filetoopen,"r")  #"/var/log/domogik/knx.txt","r")
        for ligne in fichier:
           listknx.append(ligne)
        fichier.close
        for i in range(len(listknx)):
           stat=listknx[i]
           stat=stat[stat.find("adr_stat:")+9:]
           stat=stat[:stat.find(" ")]
           print stat  
           command="groupread ip:127.0.0.1 %s" %stat
        #   subp2=subprocess.Popen(command, shell=True)
        self.log.info("Plugin ready :)")

    def send_xpl(self, data):
        """ Send xpl-trig to give status change
        """
        ### Identify the sender of the message
        command = ""
        dmgadr =""
        msg_type=""
        val=""
        sender = 'None'
        sender = data[data.find('from')+4:data.find('to')-1]
        sender = sender.strip()
        groups = 'None'
        val = 'None'
        msg_type = 'None'
        command = 'None'
        if sender<>"pageinatio":
           print "emetteur |%s|" %sender
           command = data[0:4]  
           lignetest=""
           groups = data[data.find('to')+2:data.find(':')]
           groups =":"+groups.strip()+" "
           print "groups |%s|" %groups

        ### Search the sender in the config list
           i=0
           lignetest=""
           for i in range(len(listknx)):
              if listknx[i].find(groups)>=0:
                 lignetest = listknx[i]
                 break

        ### Extract information of the configuration device  
           if lignetest<>"":
              datatype=lignetest[lignetest.find('datatype:')+9:lignetest.find(' adr_dmg')]
              dmgadr=lignetest[lignetest.find('adr_dmg:')+8:lignetest.find(' adr_cmd')]
              typeadr=lignetest[lignetest.find(groups)-4:lignetest.find(groups)]
	      typeadr=typeadr.replace("_","")
              
	      print "type d'adresse |%s|" %typeadr
              print "datatype |%s|" %datatype
              print "adresse domogik |%s|" %dmgadr
              msg=XplMessage()
              if command <> 'Read':
                 val=data[data.find(':')+1:-1]
                 val = val.strip()
                 msg_type = "s"
                 if data[-2:-1]==" ":
                    msg_type = "l"

                 if datatype == "1.001":
                    val=int(val.replace(" ",""),16)
                    if val>=1:
                       val=val
                    else:
                       self.log.error("DPT_switch 1.001 invalid value %s from %s" %(val,groups))

                 if datatype=="1.008": #"DT_UpDown":
                    val=int(val.replace(" ",""),16)
                    if val<=1:        
                       if val==1:
                          #val="down" 
                          value=0
                       if val==0:
                          #val="up"
                          value=1
                       val=value
                       print "valeur après modif %s" %val

                 if datatype =="5.001": # "DT_Scaling":
                    print "DT_Scaling"
                    val=int(val.replace(" ",""),16)
                    if val<=255:
                       val=int(100*int(val)/255)
                       print "reception DT_Scaling val=%s" %val
                    else:
                       self.log.error("DT_Scaling invalide value %s from %s" %(val,groups))

                 if datatype == "5.xxx": #8bit unsigned integer (from 0 to 255) (EIS6) 
                    val=int(val.replace(" ",""),16)
                    if val<=255:
                       val=val

                 if datatype == "5.003": #angle (from 0 to 360°) 
                    val=int(val.replace(" ",""),16)
                    print "send_xpl DT Angle"
                    if val<=255:
                       val=val*360/255
                    else:
                       self.log.error("DPT_Angle not valid argument %s from %s" %(val,groups))

                 if datatype =="6.xxx": #8bit signed integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=255:
                       val=val-128
		    else:
                       self.log.error("define 8bit signed integer overflow %s from %s" %(val,groups))

                 if datatype =="7.xxx": #16bit unsigned integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=65535:
                       val=val
                    else:
                       self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))

                 if datatype =="8.xxx": #16bit signed integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=65535:
                       val=val-32768
                    else:
                       self.log.error("define 16bit signed integer overflow %s from %s" %(val,groups))

                 if datatype =="9.xxx": #16bit unsigned integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=65535:
                       val=bin(Val)[2:]
                       if len(val)<=16:
                          for i in range(16-len(val)):
                             val="0"+val
                       Y=long(val[1:5],2)
                       X=long(val[0:1]+val[5:16],2)
                       print "Valeur de X=%s" %x
                       if X>=2047:
                          print "ce nombre semble negatif"
                          X=X-4096
                       Valeur=float(0.01*X*2**Y)
                    else:
                       self.log.error("define 16bit floating overflow %s from %s" %(val,groups))

                 if datatype =="10.001": #time (EIS3)
                    val=int(val.replace(" ",""),16)
                    if val<=3476283:
                       val=int(val.replace(" ",""),16)
                       val=bin(val)[2:]
                       second=int(val[len(val)-6:len(val)],2)
                       val=val[0:len(val)-8]
                       minute=int(val[len(val)-6:len(val)],2)
                       val=val[0:len(val)-8]
                       hour=int(val[len(val)-5:len(val)],2)
                       val=val[0:len(val)-5]
                       if len(val)>=1:
                          day=int(val,2)
                       else:
                          day="No day"
                       val=hour+":"+minute+":"+second+".0"
                    else:
                       self.log.error("define 16bit floating overflow %s from %s" %(val,groups))

                 if datatype =="11.001": #date (EIS4)
                    val=int(val.replace(" ",""),16)
                    if val<=3476283:
                       val=bin(val)[2:]
                       year=int(val[len(val)-7:len(val)],2)
                       val=val[0:len(val)-8]
                       mounth=int(val[len(val)-4:len(val)],2)
                       val=val[0:len(val)-8]
                       day=int(val[len(val)-5:len(val)],2)
                       val=year+"-"+mounth+"-"+day
                    else:
                       self.log.error("define 16bit floating overflow %s from %s" %(val,groups))
                 
                 if datatype == "12.xxx": #32 bit unsigned interger
                    val=int(val.replace(" ",""),16)
                    if val>=4294967296:
                       self.log.error("define 32 bit unsignet integer owerflow %s from %s" %(val,groups))

                 if datatype == "13.xxx": #32bit signed integer
                     val=int(val.replace(" ",""),16)
                     if val<=4294967295:
                        val=val-2147483648
                     else:
                       self.log.error("define 32 bit unsignet integer owerflow %s from %s" %(val,groups))

                 if datatype == "14.xxx": #32bit IEEE 754 floating point number
                     val=int(val.replace(" ",""),16)
                     val=bin(val)[2:]
                     if len(val)<32:
                        for i in range(32-len(val)):
                           val="0"+val
                        signe=1-2*int(val[:1])
                        exposant=str(val[1:9])
                        mantisse=str(val[9:32])
                        #signe= int(str(signe),2)
                        exposant= int(str(exposant),2)
                        mantise=0
                        for i in range(23):
                           valut=mantisse[i-1:i]
                           if valut=="1":
                              mantise=float(mantise+2**(-i))
                        mantisse= 1+mantise
                        val=float(signe*mantisse*2**(exposant-127))
                        print "résultat %s" %(signe*mantisse*2**(exposant-127))

                 if datatype =="16.xxx": #String
                    val=val.replace(" ","")
                    if len(val)/2==14:
                       phrase=""
                       for i in range(len(foo)/2):
                          phrase=phrase+ chr(int(val[0:2],16))
                          val=val[2:]
                       val=phrase
                    else:
                       self.log.error("define as string, invalid data %s from %s" %s(val,groups))

                 if datatype == "20.102": #heating mode (comfort/standby/night/frost) 
                    val=int(val.replace(" ",""),16)
                    if val>="5":
                       val=val
                    else:
                       self.log.error("DPT_HVACMode unknow code %s from %s" %(val,groups))

                 if datatype == "DT_HVACEib":
                    val=int(val.replace(" ",""),16)
                    print "reception DT_HVAC %s" %val
                    value=val
                    if typeadr=="stat":
                       if val==value:
                          if val==2:
                             value=3
                          if val==3:
                             value=1
                          if val==4:
                             value=4
                          if val==19:
                             value=3
                          if val==17:
                             value=4
                          if val==20:
                             value=1
                    val=value
                     

                 if command == 'Writ':
                    print("knx Write xpl-trig")
                    command = 'Write'
                    msg.set_type("xpl-trig")
                    msg.set_schema('knx.basic')
                 if command == 'Resp':
                    print("knx Response xpl-stat")
                    command = 'Response'
                    if sender<>"0.0.0":
                       msg.set_type("xpl-stat")
                    else:
                       msg.set_type("xpl-trig")
                    msg.set_schema('knx.basic')
                 if command == 'Read':
                    print("knx Read xpl-cmnd")
                    if sender<>"0.0.0":
                       msg.set_type("xpl-cmnd")
                    else:
                       msg.set_type("xpl-trig")
                    msg.set_schema('knx.basic')
   
              if sender<>"0.0.0":
                 msg.add_data({'command' : command+' bus'})
              else:
                 msg.add_data({'command': command+' ack'})
              msg.add_data({'group' :  dmgadr})
              msg.add_data({'type' :  msg_type})
              msg.add_data({'data': val})
              self.myxpl.send(msg)
              print "XPL command: %s group: %s type: %s data: %s" %(command,dmgadr,msg_type,val)


    def knx_cmd(self, message):
        type_cmd = message.data['command']
        groups = message.data['group']
        groups = "adr_dmg:"+groups+" "
        ligentest=""
        valeur=message.data['data']
        print "Message XPL %s" %message
        for i in range(len(listknx)):
           if listknx[i].find(groups)>=0:
              lignetest=listknx[i]

        if lignetest<>"":
           datatype=lignetest[lignetest.find('datatype:')+9:lignetest.find(' adr_dmg')]
           cmdadr=lignetest[lignetest.find('adr_cmd:')+8:lignetest.find(' adr_stat')]
           command=""
           if lignetest.find('adr_stp:')<>-1:
              stpadr=lignetest[lignetest.find('adr_stp:')+8:]
              stpadr=stpadr[:stpadr.find(' ')]

           if type_cmd=="Write":
              print("dmg Write")
              valeur = message.data['data']
              data_type = message.data['type']
              print "valeur avant modif:%s" %valeur
              val=valeur
              if datatype =="5.xxx": #16bit unsigned integer (EIS14) 
                 val=int(val)
                 if val>=0:
                    if val<=255:
                       val=hex(val)[2:]
                       valeur=""
                       for i in range(len(val)/2):
                          valeur=valeur+" "+val[0:2]
                          val=val[2:]
                       val=valeur.strip()
                    else:
                        self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))	
		 else:
                    self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))

              if datatype=="5.001": #"DT_Scaling":
                 if valeur<>"None":
                    valeur = int(valeur)*255/100
                    valeur=hex(valeur)
                 else:
                    valeur=0

	      if datatype == "5.003": #"DT_Angle":
                    if val<=360:
                       val=int(val)*255/360
                       val=hex(val)

              if datatype =="6.xxx": #8bit signed integer (EIS14) 
                 val=int(val)
                 if val<=127:
                    if val>=-128:
                       val=val+128
                       val=hex(val)[2:]
                       valeur=""
                       for i in range(len(val)/2):
                          valeur=valeur+" "+val[0:2]
                          val=val[2:]
                       val=valeur.strip()	
		 else:
                    self.log.error("define 8bit signed integer overflow %s from %s" %(val,groups))

              if datatype =="7.xxx": #16bit unsigned integer (EIS14) 
                 val=int(val)
                 if val>=0:
                    if val<=65535:
                       val=hex(val)[2:]
                       valeur=""
                       for i in range(len(val)/2):
                          valeur=valeur+" "+val[0:2]
                          val=val[2:]
                       val=valeur.strip()
                    else:
                        self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))	
		 else:
                    self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))

              if datatype =="8.xxx": #16bit signed integer (EIS14) 
                 val=int(val)
                 if val<=32767:
                    if val>=-32768:
                       val=val+32768
                       val=hex(val)[2:]
                       valeur=""
                       for i in range(len(val)/2):
                          valeur=valeur+" "+val[0:2]
                          val=val[2:]
                       val=valeur.strip()	
                 else:
                    self.log.error("define 16bit signed integer overflow %s from %s" %(val,groups))

              if datatype =="9.xxx": #16bit floating signed (EIS14) 
                 val=val.replace(",",".")
                 val=float(val)
                 if val<0:
                    val=abs(val)
                    signe="moin"
                 tmp = int(100 * abs(val))
                 for y in range(0, 15):
                    x = tmp >> y
                    if x >= 0 and x < 2048:
                       break
                 if signe=="moin":
                    x=4096-x
                 binaireX=bin(x)[2:]
                 binairey=bin(y)[2:]
                 if len(binaireX)<=12:
                    for i in range(12-len(binaireX)):
                       binaireX="0"+binaireX
                 if len(binairey)<>4:
                    for i in range(4-len(binairey)):
                       binairey="0"+binairey
                 Valeur=str(binaireX)[0:1]+" "+str(binairey)+" "+str(binaireX)[1:]
                 Valeur=Valeur.replace(" ","")
                 Valeur=int(Valeur,2)
                 Valeur=hex(Valeur)[2:]
              else:
                 self.log.error("define 16bit signed float overflow %s from %s" %(val,groups))


              if datatype =="12.xxx": #32bit unsigned integer (EIS14) 
                 val=int(val)
                 if val>=0:
                    if val<=4294967295:
                       val=hex(val)[2:]
                       valeur=""
                       for i in range(len(val)/2):
                          valeur=valeur+" "+val[0:2]
                          val=val[2:]
                       val=valeur.strip()
                    else:
                        self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))	
		 else:
                    self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))

              if datatype == "13.xxx": #32bit signed integer
                 val=int(val)
                 if val<=2147483647:
                    if val>=-2147483648:
                       val=val+2147483648
                       val=hex(val)[2:]
                       valeur=""
                       for i in range(len(val)/2):
                          valeur=valeur+" "+val[0:2]
                          val=val[2:]
                       val=valeur.strip()	
                 else:
                    self.log.error("define 32 bit unsignet integer owerflow %s from %s" %(val,groups))

              if datatype == "16.000":
                 codage=""
                 if len(val)<=14:
                    for j in range(len(val)):
                       codage=codage+hex(ord(val[j:j+1]))[2:]
                    if len(val)<14:
                       for j in range(14-len(val)):
                          codage=codage+"00"
                    valeur=codage[:2]
                    for i in range(14):
                       valeur=valeur+" "+codage[2*(i+1):2*(i+1)+2]
                 else:
                    self.log.error("Too many character")

              if datatype=="DT_HVACEib":
                 print "Hello val=%s" %val
                 valeur=val
                 command_stp="groupswrite ip:127.0.0.1 %s 0" %stpadr
                 subp2=subprocess.Popen(command_stp,shell=True)
                 if val=="3":
                    valeur="2"
                 if val=="1":
                    valeur="3"
                 if val=="2":
                    valeur=4

              if data_type=="s":
                 command="groupswrite ip:127.0.0.1 %s %s" %(cmdadr, valeur)
              if data_type=="l":
                 command="groupwrite ip:127.0.0.1 %s %s" %(cmdadr, valeur)
           if type_cmd == "Read":
              print("dmg Read")
              command="groupread ip:127.0.0.1 %s" %cmdadr
           if type_cmd == "Response":
              print("dmg Response")
              data_type=message.data['type']
              valeur = message.data['data']
              if data_type=="s":
                 command="groupsresponse ip:127.0.0.1 %s %s" %(cmdadr,valeur)
              if data_type=="l":
                  command="groupresponse ip:127.0.0.1 %s %s" %(cmdadr,valeur)
           if command<>"":
              print "envoie de la command %s" %command
              subp=subprocess.Popen(command, shell=True)
           if command=="":
              print("erreur command non définir, type cmd= %s" %type_cmd)

if __name__ == "__main__":
    INST = KNXManager()


