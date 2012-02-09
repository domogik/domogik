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
        self.log.info("Plugin ready :)")

    def send_xpl(self, data):
        """ Send xpl-trig to give status change
        """
        ### Identify the sender of the message
        sender = 'None'
        sender = data[data.find('from')+4:data.find('to')-1]
        sender = sender.strip()
        groups = 'None'
        val = 'None'
        msg_type = 'None'
        command = 'None'
        if sender<>"pageinatio":
           print "%s" %sender
           command = data[0:4]  
           lignetest=""
           groups = data[data.find('to')+2:data.find(':')]
           groups = groups.strip()
           print "%s" %groups

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
              print "datatype %s f" %datatype
              print "adresse domogik %s f" %dmgadr
     
              if command <> 'Read':
                 val=data[data.find(':')+1:-1]
                 val = val.strip()
                 val = int(val,16)
                 msg_type = "s"
                 if data[-2:-1]==" ":
                    msg_type = "l"
                 msg = XplMessage()
                 print "send_xpl valeur avant modif: %s" %val
                 if datatype == "DT_Scaling":
                    print "send_xpl Datapoint DT_Scaling"
                    if val<=255:
                       val=int(100*int(val)/255)
                       print "reception DT_Scaling val=%s" %val
                    else:
                       self.log.error("DT_Scaling invalide value %s from %s" %(val,groups))

                 if datatype=="DT_UpDown":
                    print "send_xpl DT_UpDown" 
                    if val==1:
                       val="down" 
                    if val==0:
                       val="up"
                    print "valeur après modif %s" %val
                 if datatype == "DT_Angle":
                    print "send_xpl DT Angle"
                    val=val*360/255

                 if datatype == "DT_Percent":
                    val=val

                 if datatype == "DT_HVACMode":
                    if val>="5":
                       self.log.error("DT_HVACMode unknow code %s from %s" %(val,groups))
                 
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
                 msg.add_data({'command' : command})
              else:
                 msg.add_data({'command': command+' ack'})
              msg.add_data({'group' :  dmgadr})
              msg.add_data({'type' :  msg_type})
              msg.add_data({'data': val})
              self.myxpl.send(msg)


    def knx_cmd(self, message):
        type_cmd = message.data['command']
        groups = message.data['group']
        groups = "adr_dmg:"+groups
        ligentest=""
        print "%s" %groups
        for i in range(len(listknx)):
           if listknx[i].find(groups)>=0:
              lignetest=listknx[i]
        if lignetest<>"":
           datatype=lignetest[lignetest.find('datatype:')+9:lignetest.find(' adr_dmg')]
           cmdadr=lignetest[lignetest.find('adr_cmd:')+8:lignetest.find(' adr_stat')]
           lignetest=""
           command=""
           if type_cmd=="Write":
              print("dmg Write")
              valeur = message.data['data']
              data_type = message.data['type']
              print "valeur avant modif:%s" %valeur
              if datatype=="DT_Scaling":
                 if valeur<>"None":
                    valeur = int(valeur)*255/100
                    print("command val=%s" %valeur)
                    valeur=hex(valeur)
                    print( "%s" %valeur)
                 else:
                    valeur=0
              #else:
              #   print "Datapoint non trouver"
              #   valeur=hex(int(valeur))
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


