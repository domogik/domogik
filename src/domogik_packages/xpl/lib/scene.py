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

Mini Scene

Implements
==========

- MiniScene

@author: Fritz <fritz.smh@gmail.com> Basilic <Basilic3@hotmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import subprocess
import urllib2
import time
import threading
import ast
from domogik.xpl.common.xplconnector import *
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from socket import *

class SceneException(Exception):
    """
   # Scene exception
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)
 
class Scene:

    def __init__(self, log, callback):
        self._log = log
        self._callback = callback
        self._ser = None

    def open(self):
        """ open
            @param device :
        """
        print "ouverture du plugin"

    def close(self):
        """ close t
        """
        print "fermeture du plugin"

    def listen(self):
        """close
        """
        print "demarage du listen"
        self._read = True
        
    def stop_listen(self):
        """ rien du tout
        """
        print "arret du listen"
        self._read = False

class Mscene():
    number='0'
    gdevice1 =''
    gdevice2 =''
    gaction_true = ''
    gaction_false  = ''
    key_stat1 = ''
    key_stat2 = ''
    etat_scene= 'sleep'
    device1_stat = ''
    device2_stat = ''
    grinor=''
    listener1 = ['','','','','','','','','','']
    listener2 = ['','','','','','','','','','']
    glistener = ''

    def __init__(self,number,device1,device2,condition,Action_true,Action_false,rinor):
      self.number="scene_%s" %number

      msg=XplMessage()
      msg.set_schema('scene.basic')
      msg.set_type('xpl-trig')
      msg.add_data({'number': self.number})
      msg.add_data({'run':'Start'})
      msg.add_data({'statue':'unknow'})
      self.send(msg)
      print "fin de l'init lib envoie du XPl"
#      XplPlugin.__init__(self, name = 'send', daemonize = False, parser = None, nohub = True)

     # number is the ref of the scene
     # device1 and 2 are dictionnary where found {address, id, key_stat, listener:[{schema,device field}]}
     # condition is dicationnary where can found {test1, value1, test2,value2, test_global}
     # Action_true and false are dictionnary where found {id, command, value}
     # rinor is a string 'rinor_ip:port'

      #initialise les variables global
      self.gdevice2=device2
      self.gdevice1=device1
      self.gaction_true=Action_true
      self.gaction_false=Action_false
      self.gcondition=condition
      self.grinor= rinor

    def auother(self):
      self.glistener = Listener(self.cmd_scene,self.myxpl,{'schema':'scene.basic','xpltype':'xpl-cmnd','scene':self.number})

    def cmd_scene(self,message):
       if message.data['command']=='start':
          self.start()
       elif message.data['command']=='stop':
          self.stop()

    def start(self):
       print 'start'

    def start2(self):
       self.key_stat1 = self.device1['key_stat']

       if self.device2['id'] != '':
          self.key_stat2 = self.device2['stat']

      #initialise les device_stat1 et 2 via un rinor et cree les listeners referant a cmd_device1 et cmd_device2

       the_url = 'http://%s/stats/%s/%s/latest' %(self.rinor, self.device1['id'], self.device1['key_stat'])
       req = urllib2.Request(the_url)
       handle = urllib2.urlopen(req)
       resp1 = handle.read()
       self.device1_stat= ast.literal_eval(resp1)['stats'][0]['Value']
       self.listener1 = ['','','','','','','','','','']
       for i in range(len(device1['listener'])):
          self.listener1[i] = Listener(self.cmd_device1,self.myxpl,{'schema':device1['listener'][i]['schema'],'xpltype':'xpl-trig',device1['listener'][i]['device']:device1['address']})

       if device2["id"] != '' and device2["key_stat"] != '':
          the_url = 'http://%s/stats/%s/%s/latest' %(rinor, device2['id'], device2['key_stat'])
          req = urllib2.Request(the_url)
          handle = urllib2.urlopen(req)
          resp2 = handle.read()
          device2_stat= ast.literal_eval(resp2)['stats'][0]['Value']
          self.listener2 = ['','','','','','','','','','']
          for i in range(len(self.device2['listener'])):
             self.listener2[i]=Listener(self.cmd_device2,self.myxpl,{'schema':device2['listener'][i]['schema'],'xpltype':'xpl-trig',device2['listener'][i]['device']:device2['address']})
       msg=XplMessage()
       msg.set_schema('scene.basic')
       msg.set_type('xpl-trig')
       msg.add_data({'number': self.number})
       msg.add_data({'run':'Start'})
       msg.add_data({'statue':''})
       self.send(msg)
       self.etat_scene = self.test()

    def send(self, message):
       print 'debut du send sauvage'
       message="xpl-trig\n{\nhop=1\nsource=domogik-scene.basilicserver\ntarget=*\n}\nscene.basic\n{\ntest=2\n}\n"
       print message
       addr = ("255.255.255.255",3865)
       UDPSock = socket(AF_INET,SOCK_DGRAM)
       UDPSock.setsockopt(SOL_SOCKET,SO_BROADCAST,1)
       UDPSock.sendto(message.__str__(),addr)
       print 'send sauvage ok'

    def stop(self):
       for j in range(len(self.listener1)):
          if self.listener1[j] != '':
             self.myxpl.del_listener(self.listener1[j])
          if self.listener2[j] != '':
             self.myxpl.del_listener(self.listener2[j])
       msg=XplMessage()
       msg.set_schema('scene.basic')
       msg.set_type('xpl-trig')
       msg.add_data({'number': self.number})
       msg.add_data({'run':'Stop'})
       msg.add_data({'statue':''})
       self.myxpl.send(msg)

    def cmd_device2(self, message):
       self.device1_stat=message.data[self.key_stat1]
       self.etat_scene = self.test()

    def cmd_device2(self, message):
       self.device2_stat=message.data[self.key_stat2]
       self.etat_scene = self.test()

    def test(self):
       # function was call when an xpl-trig for on of device was receve
       last_value = self.etat_scene
       condition = 'none'
       condition1= 'none'
       condition2= 'none'
       if self.gcondition['test1'] != '' and self.gcondition['value1'] != '' :
          if self.gcondition['test1']=='=':
             if self.device1_stat == gcondition['value1']:
                condition1='true'
             else:
                condition1='false'
          elif self.gcondition['test1']=='<':
             if self.device1_stat < gcondition['value1']:
                condition1='true'
             else:
                condition1='false'
          elif self.gcondition['test1']=='>':
             if self.device1_stat > gcondition['value1']:
                condition1='true'
             else:
                condition1='false'
          elif self.gcondition['test1']=='!=':
             if self.device1_stat != gcondition['value1']:
                condition1='true'
             else:
                condition1='false'

       if self.gcondition['test2'] != '' and self.gcondition['value2'] != '' :
          if self.gcondition['test2']== '=':
             if self.device2_stat == gcondition['value2']:
                condition2='true'
             else:
                condition2='false'
          elif self.gcondition['test2']== '<':
             if self.device2_stat < gcondition['value2']:
                condition2='true'
             else:
                condition2='false'
          elif self.gcondition['test2']== '>':
             if self.device2_stat > gcondition['value2']:
                condition2='true'
             else:
                condition2='false'
          elif self.gcondition['test2']== '!=':
             if self.device2_stat != gcondition['value2']:
                condition2='true'
             else:
                condition2='false'

       if self.gcondition['test_global'] != '':
          if self.gcondition['test_global']=='=':
             if self.device1_stat == self.device2_stat:
                condition = 'true'
             else:
                condition = 'false'
          elif self.gcondition['test_global']== '<':
             if self.device1_stat <  self.device2_stat:
                condition = 'true'
             else:
                condition = 'false'
          elif self.gcondition['test_global']== '>':
             if self.device1_stat >  self.device2_stat:
                condition = 'true'
             else:
                condition = 'false'
          elif self.gcondition['test_global']== '!=':
             if self.device1_stat !=  self.device2_stat:
                condition2 = 'true'
             else:
                condition2 = 'false'
          elif self.gcondition['test_global']== 'and':
             if condition1 == 'true' and condition2 == 'true':
                condition = 'true'
             else:
                condition = 'false'
          elif self.gcondition['test_global']== 'or':
             if condition1 == 'true' or condition2 == 'true':
                condition = 'true'
             else:
                condition = 'false'
          # cas d'un ou exclusif l'un ou l'autre mais pas les 2
          elif self.gcondition['test_global']== '!or':
             if (condition1 == 'true' and condition2 == 'false') or (condition1 == 'false' and condition2 == 'true'):
                condition = 'true'
             else:
                condition = 'false'
       else:
          condition=condition1

       if condition == 'true' and condition != last_value:
         # envoie de la commande true
#         http://ip:port/command/<technology>/<address>/<command>/command [/...]
          the_url = 'http://%s/command/%s/%s/%s' %(grinor, gaction_true['techno'], gaction_true['address'], gaction_true['value'])
          req = urllib2.Request(the_url)
          handle = urllib2.urlopen(req)
          resp1 = handle.read()
          msg=XplMessage()
          msg.set_schema('scene.basic')
          msg.set_type('xpl-trig')
          msg.add_data({'number': 'scene_' + self.number})
          msg.add_data({'run':'OK'})
          msg.add_data({'statue':'true'})
          myxpl.send(msg)

       if contition == 'false' and condition != last_value:
         # envoie de la commande false
          the_url = 'http://%s/command/%s/%s/%s' %(grinor, gaction_false['techno'], gaction_false['address'], gaction_false['value'])
          req = urllib2.Request(the_url)
          handle = urllib2.urlopen(req)
          resp1 = handle.read()
          msg=XplMessage()
          msg.set_schema('scene.basic')
          msg.set_type('xpl-trig')
          msg.add_data({'number': 'scene_' + self.number})
          msg.add_data({'run':'OK'})
          msg.add_data({'statue':'false'})
          myxpl.send(msg)

       if condition == last_value:
          msg=XplMessage()
          msg.set_schema('scene.basic')
          msg.set_type('xpl-stat')
          msg.add_data({'number': 'scene_' + self.number})
          msg.add_data({'run':'OK'})
          msg.add_data({'statue': condition})

       return condition

def decode(message):
    """ dédage du message
    """
    print "%s" % message

if __name__ == "__main__":                                                      
                                                     
    obj = Scene(None, decode)
    obj.open()
    obj.listen()           


    
       


