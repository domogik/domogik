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
from domogik.common.configloader import *

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


    def read_scene(self,filetoopen):
        """ read all ligne in scene file
        """
        e=open(filetoopen,"r")
        o=e.read().split("\n")
        e.close()
        return o
        
    def delete_scene(self,filetoopen, ligne):
        """ Add ligne to scene file
        """
        e=open(filetoopen,"w")
        o=e.read().split("\n")
        e.close()
        f=open(filetoopen,"w")
        ligne=int(valeur,10)-1
        print ligne
        for i in range(len(o)):
           if i!=ligne:
              if o[i]!="":
                 f.write(o[i]+"\n")
              else:
                 print "ligne a supprimer:|%s|" %o[ligne]
                 testy=str(o[ligne])+"\n"
              print o[i]
        f.close()

    def add_scene(self,filetoopen,ligne):
        """ Add a ligne to scene fle
        """
        fichier=open(filetoopen,"a")
        fichier.write(ligne)

class Mscene():
   
### devices is a dictionnary with all device
##### device is a dictionnary with keys: name, id, address,techno, key_stat, op, value, filters
####### filters is a list with filter

### Conditions beetwen 2 devices need define how...

### Action_true is a list with all action in dictionnary form, dictionnary key is address,techno, command and value
### Action_false is same as Action_true but for else case

    def __init__(self,number,xplmanager,devices,condition,Action_true,Action_false,rinor,host):
      #initialise les variables global
      self.number="scene_%s" %number
      self.myxpl=xplmanager
      self.senderscene = "domogik-scene%s.%s" %(number,host)
      self.senderplug = "domogik-scene.%s" %host
      self.devices_stat={}
      self.devices_test={}
      self.gaction_true=Action_true
      self.gaction_false=Action_false
      self.gcondition=condition
      self.grinor= rinor
      condition_formulate()
      for device in devices:
         self.devices_stat[device]=''
      send_msg_plugin(self, "Stop", 'None'):
      self.initstat='1' #this variable enable or desable the launch command as init
      self.glistener = Listener(self.cmd_scene,self.myxpl,{'schema':'scene.basic','xpltype':'xpl-cmnd','number':self.number})  #listerner of the scene

    def cmd_scene(self,message):
       if message.type == "xpl-cmnd":
          if message.data['command']=='start':
             self.scene_start()
          elif message.data['command']=='stop':
             self.scene_stop()
          elif message.data['command']=='delete':
             self.scene_delete()

    def send_msg_plugin(self, run, stats):
### send a message with the plugin name as source
       msg=XplMessage()
       msg.set_source(self.senderplug)
       msg.set_schema('scene.basic')
       msg.set_type('xpl-trig')
       msg.add_data({'number': self.number})
       msg.add_data({'run':run})
       msg.add_data({'stats':stats})
       self.myxpl.send(msg)

    def send_msg_scene(self,type, run, stats):
### send a message with the scene name as source
       msg=XplMessage()
       msg.set_source(self.senderscene)
       msg.set_schema('scene.basic')
       msg.set_type(type)
       msg.add_data({'number': self.number})
       msg.add_data({'run':run})
       msg.add_data({'stats':stats})
       self.myxpl.send(msg)

    def get_stat(self):
### get last stat for a device, argument need is a device_id and the device_keystat
       for device in devices:
          the_url = 'http://%s/stats/%s/%s/latest' %(self.grinor, self.devices[device]['id'], self.devices[devices]['key_stat'])
          req = urllib2.Request(the_url)
          handle = urllib2.urlopen(req)
          resp = handle.read()
          self.devices_stat[device]= ast.literal_eval(resp)['stats'][0]['value']

    def start_listerner(self):
       for device in devices:
          for i in range(len(self.devices[device]['filters']):
             list=Listener(self.cmd_device,self.myxpl,{'schema':self.devices[device]['filters'][i]['schema'],'xpltype':'xpl-trig',self.devices[device]['filters'][i]['device']:self.devices[device]['address']})


    def scene_start(self):
###initialise all device_stat et les listerners
       self.get_stat()
       self.start_listerner()
 
       send_msg_plugin(self, 'start', 'None')

       self.etat_scene = self.test()
       
    def scene_delete(self):
### stop device listerner and del scene listerner
        self.stop()
        self.myxpl.del_listener(self.glistener)
        #TODO add delete file and rinor delete device scene if exist

    def scene_stop(self):
### del all devices listerner
       for element in self.listener:
          self.myxpl.del_listener(element)

       self.send_msg_plugin('stop','None')

    def cmd_device(self, message):
### get the stat of message and place it in devices_stat
       for device in self.devices:
           if devices[device]['xpl_stat'] in message.data and device[device['adr']] in message.data:
              self.devices_stat[device]=message.data[device['xpl_stat']]

    def send_command(self, actions):
### send to rinor all actions define in 'actions'
       for action in actions:
          if actions[action]['techno'] == 'command' and actions[action]['address']== 'command' and actions[action]['command']=='command':
             subp = subprocess.Popen(self.gaction_true['value'], shell=True) 
          if actions[action]['techno'] != 'send-xpl':
             send_action_xpl(actions[action])
          if actions[action]['techno'] != 'command' and actions[action]['techno'] != 'send-xpl':
             self.rinor_command(actions[action])
          
    def send_action_xpl(self, action):
### Send an xpl message define in scene action
     ### action['type_message'] =xpl-type
     ### action['schema'] = xpl schema
     ### action['value'] = xpl val
       msg=XplMessage()
       msg.set_source(self.senderscene)
       msg.set_schema(action['schema'])
       msg.set_type(action['type_message'])
       msg.add_data(action['value'])
       self.myxpl.send(msg)

    def rinor_command(self,action):
### send rinot action
        if actions[action]['command']=='':
           the_url = 'http://%s/command/%s/%s/%s' %(self.grinor, actions[action]['techno'], actions[action]['address'], actions[action]['value'])
        else:
           the_url = 'http://%s/command/%s/%s/%s/%s' %(self.grinor, self.gaction_true['techno'], actions[action]['address'],actions[action]['command'],actions[action]['value'])

         if self.initstat != '1':
            req = urllib2.Request(the_url)
            handle = urllib2.urlopen(req)
            resp1 = handle.read()


    def device_test(self):
### test devices value and evaluate result
        for device in self.devices:
           if self.devices[device]['op'] != '':
              if self.devices[device]['op'] == '=':
                 if self.devices_stat[device] == self.devices[device]['value']
                    self.devices_test[device]= True
                 else:
                    self.devices_test[device]= False
              elif self.devices[device]['op'] == '>':
                 if self.devices_stat[device] > self.devices[device]['value']
                    self.devices_test[device]= True
                 else:
                    self.devices_test[device]= False
              elif self.devices[device]['op'] == '<':
                 if self.devices_stat[device] < self.devices[device]['value']
                    self.devices_test[device]= True         
                 else:
                    self.devices_test[device]= False
           else:
              self.devices_test[device]=self.devices_stat[device]

        last_value=self.gcondition
        new_value = eval(self.gcondition)

        if last_value != new_value:
           if new_value == True:
              ### TODO send command and xpl-trig
           if new_value == False:
              ### TODO send command and xpl-trig
        else:
           if new_value == True:
              ### TODO send xpl-stat
           if new_value == False:
              ### TODO send xpl-stat

   def condition_formulate(self,condition):
### correction of condition test to do a correct test
       condition = condition.lower()
       condition = condition.replace('(', ' ( ')
       condition = condition.replace(')', ' ) ')
       condition = " "+ condition + " "
       condition = condition.replace('<=', ' <= ')
       condition = condition.replace('==', ' == ')
       condition = condition.replace('>=', ' >= ')
       condition = condition.replace('!=', ' != ')
       condition = condition.replace('<>', ' != ')
       condition = condition.replace('xor', ' ^ ')
       condition = condition.replace('nand', ' and not ')
       condition = condition.replace('nor', ' or not ')
       condition = condition.replace(' = ',' == ')

       for i in range(100):
          device_av = "device%s " %i
          device_ap = "devices_test[device%s] " %i
          condition = condition.replace(device_av, device_ap)

       " ".join(conditon.split())
       return condition
