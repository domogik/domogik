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
@copyright: (C) 2007-2012 Domogik project
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
from struct import * 
import threading
import subprocess
from time import *
from binascii import *

listknx=[]

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
#        device = self._config.query('knx', 'device')

        ### Create KNX object
        try:
            self.knx = KNX(self.log, self.send_xpl)
            self.log.info("Open KNX")
 #           self.knx.open(device)

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
        whereisfile='locate "*/data/knx.txt"'
        print whereisfile
        subpp=subprocess.Popen(whereisfile,shell=True)
        print "||%s||" %subpp
        fichier=open(filetoopen,"r")
        for ligne in fichier:
           if ligne[:1]<>"#":
              listknx.append(ligne)
              print ligne
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
        lignetest=""
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
              
              msg=XplMessage()
              if command <> 'Read':
                 print "%s %s" %(typeadr,command)
                 val=data[data.find(':')+1:-1]
                 val = val.strip()
                 print "-%s|" %val
                 msg_type = "s"
                 if data[-2:-1]==" ":
                    msg_type = "l"

                 if datatype == "1.001": #DT_switch
                    val=int(val.replace(" ",""),16)
                    print "Switch"
                    if val==1:
                       val="on"
                    if val==0:
                       val="off"
                    if val>=2:
                       self.log.error("DPT_switch 1.001 invalid value %s from %s" %(val,groups))

                 if datatype=="1.008": #"DT_UpDown":
                    print "Shutter"
                    val=int(val.replace(" ",""),16)
                    if val<=1:        
                       if val==1:
                          val="Down"
                       if val==0:
                          val="Up"

                 if datatype == "3.007": #DT_Control_Dimming
                    val=int(val)
                    if val>=1 and val <= 7:
                       val= "dim-"
                    if val>=9:
                       val="dim+"
                    if val==8 or val==0:
                       val="stop"

                 if datatype == "3.008": #DT_Control_Blinds
                    val=int(val)
                    if val>=1 and val <= 7:
                       val= "up"
                    if val>=9:
                       val="down"
                    if val==8 or val==0:
                       val="stop"


                 if datatype =="5.001": # "DT_Scaling":
                    print "DT_Scaling"
                    val=int(val.replace(" ",""),16)
                    if val<=255:
                       val=(100*int(val)/255)
                    else:
                       self.log.error("DT_Scaling invalide value %s from %s" %(val,groups))

                 if datatype[:2] == "5." and  datatype!="5.001" and datatype!="5.003": #8bit unsigned integer
                    val=int(val.replace(" ",""),16)
                    if val<=255:
                       val=val

                 if datatype == "5.003": #DT_Angle
                    val=int(val.replace(" ",""),16)
                    print "send_xpl DT Angle %s" %val
                    if val<=255:
                       val=val*360/255
                       print val
                    else:
                       self.log.error("DPT_Angle not valid argument %s from %s" %(val,groups))

                 if datatype[:2] =="6.": #8bit signed integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=255:
                       if val<128:
                          val=val
                       else:
                          val=val-256
		    else:
                       self.log.error("define 8bit signed integer overflow %s from %s" %(val,groups))

                 if datatype[:2] =="7.": #16bit unsigned integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=65535:
                       val=val
                    else:
                       self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))

                 if datatype[:2] =="8.": #16bit signed integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=65535:
                       if val<=32767:
                          val=val
                       else:
                          val=-65536+val
                    else:
                       self.log.error("define 16bit signed integer overflow %s from %s" %(val,groups))

                 if datatype[:2] =="9.": #16bit unsigned integer (EIS14) 
                    val=int(val.replace(" ",""),16)
                    if val<=65535:
                       val=bin(val)[2:]
                       if len(val)<=16:
                          for i in range(16-len(val)):
                             val="0"+val
                       Y=long(val[1:5],2)
                       X=long(val[0:1]+val[5:16],2)
                       print "Valeur de X=%s" %X
                       if X>=2047:
                          print "ce nombre semble negatif"
                          X=X-4096
                       val=float(0.01*X*2**Y)
                    else:
                       self.log.error("define 16bit floating overflow %s from %s" %(val,groups))

                 if datatype =="10.001": #time (EIS3)
                    val=int(val.replace(" ",""),16)
                    if val!=0: #val<=347628                       
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
                       if len(str(hour))<2:
                          hour="0"+str(hour)
                       if len(str(minute))<2:
                          minute="0"+minute
                       if len(str(second))<2:
                          second="0"+second
                       val=str(hour)+":"+str(minute)+":"+str(second)+".0"
                       print "heure: %s" %val
                    else:
                       self.log.error("define 16bit floating overflow %s from %s" %(val,groups))

                 if datatype =="11.001": #date (EIS4)
                    val=int(val.replace(" ",""),16)
                    if val!=0:
                       val=bin(val)[2:]
                       if len(val)<24:
                          for i in range(24-len(val)):
                             val="0"+val
                       year=int(val[len(val)-7:len(val)],2)
                       val=val[0:len(val)-8]
                       mounth=int(val[len(val)-4:len(val)],2)
                       val=val[0:len(val)-8]
                       day=int(val[len(val)-5:len(val)],2)
                       if len(str(year))<2:
                          year="0"+str(year)
                       if len(str(mounth))<2:
                          mounth="0"+str(mounth)
                       if len(str(day))<2:
                          day="0"+str(day)
                       val=str(year)+"-"+str(mounth)+"-"+str(day)
                    else:
                       self.log.error("define 16bit floating overflow %s from %s" %(val,groups))
                 
                 if datatype[:3] == "12.": #32 bit unsigned interger
                    val=int(val.replace(" ",""),16)
                    if val>=4294967296:
                       val=val
                    else:
                       self.log.error("define 32 bit unsignet integer owerflow %s from %s" %(val,groups))

                 if datatype[:3] == "13.": #32bit signed integer
                     val=int(val.replace(" ",""),16)
                     if val<=4294967295:
                        if val<=2147483647:
                           val=val
                        else:
                           val=-4294967295+val
                     else:
                       self.log.error("define 32 bit unsignet integer owerflow %s from %s" %(val,groups))

                 if datatype[:3] == "14.": #32bit IEEE 754 floating point number
                     val=int(val.replace(" ",""),16)
                     val= unpack('f',pack('I',val))[0]
                     print val

                 if datatype[:3] =="16.": #String
                    val=val.replace(" ","")
		    if len(val)/2==14:
                       phrase=""
                       for i in range(len(val)/2):
                          phrase=phrase+ chr(int(val[0:2],16))
                          val=val[2:]
                       val=phrase
                    else:
                       self.log.error("define as string, invalid data %s from %s" %(val,groups))

                 if datatype == "20.102": #heating mode (comfort/standby/night/frost) 
                    val=int(val.replace(" ",""),16)
                    if val==20 or val==28:
                       val="HVACnormal" #1
                    if val==19 or val==24:
                       val="HVACeco" #3
                    if val==7:
                       val="HVACnofreeze" #4
                    if val==26:
                       val="HVACstop" #2

                 if datatype == "DT_HVACEib":
                    val=int(val.replace(" ",""),16)
                    print "reception DT_HVAC %s" %val
                    value="DT_HVACEib"
                    if val==2 or val==19:
                       value="HVACeco"
                    if val==3 or val==20:
                       value="HVACnormal"
                    if val==4 or val==17:
                       value="HVACnofreeze"
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
              print "sender: %s typeadr:%s" %(sender, typeadr)
              if sender=="0.0.0" and typeadr=="cmd":
                 self.myxpl.send(msg)
                 print "XPL command: %s group: %s type: %s data: %s" %(command,dmgadr,msg_type,val)
              if typeadr=="stat":
                 self.myxpl.send(msg)
                 print "Envoie d'une stat"

    def knx_cmd(self, message):
        type_cmd = message.data['command']
        groups = message.data['group']
        groups = "adr_dmg:"+groups+" "
        lignetest=""
        valeur=message.data['data']
        print "Message XPL %s" %message
        for i in range(len(listknx)):
           if listknx[i].find(groups)>=0:
              lignetest=listknx[i]
        print "ligne test=|%s|" %lignetest
        if lignetest<>"":
           datatype=lignetest[lignetest.find('datatype:')+9:lignetest.find(' adr_dmg')]
           cmdadr=lignetest[lignetest.find('adr_cmd:')+8:lignetest.find(' adr_stat')]
           command=""
           print "Command: |%s|" %type_cmd
           print "Groups: |%s|" %cmdadr
           print "datatype: |%s|" %datatype
           print "valeur avant codage: |%s|" %valeur

           if lignetest.find('adr_stp:')<>-1:
              stpadr=lignetest[lignetest.find('adr_stp:')+8:]
              stpadr=stpadr[:stpadr.find(' ')]

           if type_cmd=="Write":
              print("dmg Write %s") %type_cmd
              valeur = message.data['data']
              data_type = message.data['type']
              print "valeur avant modif:%s" %valeur
              val=valeur

              if datatype =="1.001":
                 data_type="s"
                 if val == "on" or val == "1":
                    valeur=1
                 if val == "off" or val == "0":
                    valeur=0

              if datatype == "1.008":
                 data_type="s"
                 if val == "up" or val == "0":
                    valeur=0
                 if val == "down" or val ==1:
                    valeur=1

              if datatype =="3.007":
                 data_type="s"
                 if val=="dim+":
                    valeur="9"
                 if val == "dim-":
                    valeur="1"
                 if val=="stop+":
                    valeur=8
                 if val=="stop-":
                    valeur=0

              if datatype =="3.008":
                 data_type="s"
                 if val=="downstep":
                    valeur="9"
                 if val == "upstep":
                    valeur="1"
                 if val=="downstop":
                    valeur=8
                 if val=="upstop":
                    valeur=0

              if datatype[:2] =="5." and datatype!="5.001" and datatype!="5.003": #8bit unsignet int 
                 val=int(val)
                 data_type="l"
                 if val>=0 and val<=255:
                    val=hex(val)[2:]
                    valeur=""
                    for i in range(len(val)/2):
                       valeur=valeur+" "+val[0:2]
                    valeur=valeur.strip()
                 else:
                    self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))

              if datatype == '5.001':
                 data_type="l"
                 print 'envoie d un pourcent'
                 if val<>"None":
                    val = int(valeur)*255/100
                    valeur=hex(val)[2:]
                 else:
                    valeur=0

	      if datatype == "5.003":
                 data_type="l"
                 print 'envoie d un angle %s' %val
                 val=int(val)
                 if val<=360 and val>=0:
                    val=int(val)*255/360
                    print val
                    valeur=hex(val)

              if datatype[:2] == "6.": #8bit signed integer (EIS14) 
                 data_type="l"
                 val=int(val)
                 print "|%s|" %val
                 if val<=127 and val>=-128:
                    if val<0:
                       val=256+val
                    valeur=hex(val)[2:]	
		 else:
                    self.log.error("define 8bit signed integer overflow %s from %s" %(val,groups))

              if datatype[:2] == "7.": #16bit unsigned integer (EIS14) 
                 data_type="l"
                 val=int(val)
                 if val>=0 and val<=65535:
                    val=hex(val)[2:]
                    valeur=""
                    if len(val)<4:
                       for i in range(4-len(val)):
                          val="0"+val
                    valeur=val[:2]+" "+val[2:4]                      
                    print "Valeur 16 bit unsigned val=|%s|" %valeur
                 else:
                    self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))	

              if datatype[:2] == "8.": #16bit signed integer (EIS14) 
                 data_type="l"
                 val=int(val)
                 if val<=32767 and val>=-32768:
                    if val<0:
                       val=65536+val
                    val=hex(val)[2:]
                    valeur=val[:2]+" "+val[2:4]
                 else:
                    self.log.error("define 16bit signed integer overflow %s from %s" %(val,groups))

              if datatype[:2] == "9.": #16bit floating signed (EIS14) 
                 data_type="l"
                 val=val.replace(",",".")
                 signe="plus"
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
                 valeur=str(binaireX)[0:1]+" "+str(binairey)+" "+str(binaireX)[1:]
                 valeur=valeur.replace(" ","")
                 valeur=int(valeur,2)
                 valeur=hex(valeur)[2:]
                 if len(valeur)<4:
                    for i in range(4-len(valeur)):
                       valeur="0"+valeur
                 valeur=valeur[:2]+" "+valeur[2:4]

              if datatype == "10.001": #time
                 data_type="l"
                 hour=int(strftime('%H',localtime()))
                 minute=int(strftime('%M',localtime()))
                 seconde=int(strftime('%S',localtime()))
                 weekday=int(strftime('%w',localtime()))
                 hour=bin(hour)[2:]
                 minute=hex(minute)[2:]
                 weekday=bin(weekday)[2:]
                 seconde=hex(seconde)[2:]
                 if len(hour)<5:
                    for i in range(5-len(hour)):
                       hour="0"+hour
                 if len(weekday)<3:
                    for i in range(3-len(weekday)):
                       weekday="0"+weekday
                 if len(minute)<2:
                    minute="0"+minute
                 if len(seconde)<2:
                    seconde="0"+seconde
                 dayhour=weekday+hour
                 dayhour=hex(int(dayhour,2))[2:]
                 valeur=str(dayhour)+" "+str(minute)+" "+str(seconde)

              if datatype == "11.001": #Date
                 data_type="l"
                 dayofmounth=hex(int(strftime('%d',localtime())))[2:]
                 mounth=hex(int(strftime('%m',localtime())))[2:]
                 years=hex(int(strftime('%y',localtime())))[2:]
                 if len(dayofmounth)<2:
                    dayofmounth="0"+dayofmounth
                 if len(mounth)<2:
                    mounth="0"+mounth
                 if len(years)<2:
                    years="0"+years
                 valeur=dayofmounth+" "+mounth+" "+years


              if datatype[:3] == "12.": #32bit unsigned integer (EIS14) 
                 data_type="l"
                 val=int(val)
                 if val>=0 and val<=4294967295:
                    val=hex(val)[2:]
                    if len(val)<8:
                       for i in range(8-len(val)):
                          val="0"+val                    
                    valeur=val.strip()
                    valeur=valeur[:2]+" "+valeur[2:4]+" "+valeur[4:6]+" "+valeur[6:8]
                 else:
                     self.log.error("define 16bit unsigned integer overflow %s from %s" %(val,groups))

              if datatype[:3] == "13.": #32bit signed integer
                 data_type="l"
                 val=int(val)
                 if val<=2147483647 and val>=-2147483648:
                    if val<0:
                       val=4294967295+val
                    val=hex(val)[2:]
                    if len(val)<8:
                       for i in range(8-len(val)):
                          val="0"+val
                    valeur=val.strip()
                    valeur=valeur[:2]+" "+valeur[2:4]+" "+valeur[4:6]+" "+valeur[6:8]
                 else:
                    self.log.error("define 32 bit unsignet integer owerflow %s from %s" %(val,groups))

              if datatype == "14.001": #IEE754 floating
                 data_type="l"
                 print "valeur 14.001 %s" %val
                 val=float(val)
                 valeur=hexlify(pack('>f',val))
                 print "IEE754 %s" %valeur
                 if len(valeur)==8:
                    valeur=valeur[0:2]+" "+valeur[2:4]+" "+valeur[4:6]+" "+valeur[6:8]
                 else:
                    self.log.erreur("Variable len(valeur) infusffisante")              
                    valuer=""
                 print valeur

              if datatype == "16.000": #string
                 data_type="l"
                 codage=""
                 text=val
                 for j in range(int(len(val)/14)+1):
                    val=text[j*14:j*14+14]
                    codage=""
                    if len(val)<=14:
                       for j in range(len(val)):
                          codage=codage+" "+hex(ord(val[j:j+1]))[2:]
                       if len(val)<14:
                          for j in range(14-len(val)):
                             codage=codage+" 00"
                       print codage
                       command="groupwrite ip:127.0.0.1 %s %s" %(cmdadr,codage)
                       subp2=subprocess.Popen(command,shell=True)
                    else:
                       self.log.error("Too many character")
                 type_cmd="None" 

              if datatype == "20.102": #HVAC Mode
                 if val == "1" or val == "HVACnormal":
                    valeur=1
                 if val == "2" or val == "HVACstop":
                    valeur=2
                 if val == "3" or val == "HVACeco":
                    valeur=3
                 if val == "4" or val == "HVACnofreeze":
                    valeur=4

              if datatype == "DT_HVACEib": #Datapoint type for TB042
                 data_type="l"
                 if val == "4" or val == "HVACnofreeze":
                    valeur=4
                 if val == "3" or val == "HVACeco":
                    valeur="2"
                 if val == "1" or val == "HVACnormal":
                    valeur="3"
                 if val == "2" or val == "HVACstop":
                    valeur=4

              print "Valeur modifier |%s|" %valeur
              
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

        ### ajout d'un device dans le fichier de configuration du KNX

        if type_cmd=="Add":
           print "Add device"
           valeur=valeur[1:]
           Adr_dmg=valeur[:valeur.find(",")]
           valeur=valeur[valeur.find(",")+1:]
           dptype=valeur[:valeur.find(",")]
           valeur=valeur[valeur.find(",")+1:]
           Adr_cmd=valeur[:valeur.find(",:")]
           valeur=valeur[valeur.find(",")+1:]
           Adr_stat=valeur[:-1]

           filetoopen=self._config.query('knx','file')
           print filetoopen

           fichier=open(filetoopen,"a")
           ligne="datatype:%s adr_dmg:%s adr_cmd:%s adr_stat:%s end \n" %(dptype,Adr_dmg,Adr_cmd,Adr_stat)
           print ligne
           fichier.write(ligne)
           fichier.close
           listknx.append(ligne)


if __name__ == "__main__":
    INST = KNXManager()
