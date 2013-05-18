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
import glob
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
        print("ouverture du plugin")

    def close(self):
        """ close t
        """
        print("fermeture du plugin")

    def listen(self):
        """close
        """
        print("demarage du listen")
        self._read = True
        
    def stop_listen(self):
        """ rien du tout
        """
        print("arret du listen")
        self._read = False


    def read_all(self,Path):
        """ read all ligne in scene file
        """
        all_scene={}
        for file in glob.iglob(Path+"/*.scn") :
            config = ConfigParser.ConfigParser()
            config.read(file)
            scene={}
            scene_numb= "scene_" + config.get('Scene','name')
            self._log.info("Open for read file %s" %scene_numb)
            for section in config.sections():
               data={}
               for option in config.options(section):
                  data[option] = config.get(section, option)
               scene[section]=data
            all_scene[scene_numb]=scene
        return all_scene
        
    def delete_scene(self,file):
        """ Delete a scene file
        """
        self._log.info("Remove file: %s" %file)
        try:
           os.remove(file)
        except:
           self._log.error("Impossible to remove %s" %file)
        
    def add_scene(self,data):
        """ Add a scene file
        """
        file=ConfigParser.ConfigParser()
        scene_file = data['Scene']['file']
        
        file.add_section('Scene')
        for value in data['Scene']:
           file.set('Scene',value, data['Scene'][value])
        for device in data['devices']:
           file.add_section(str(device))
           for value in data['devices'][device]:
              file.set(str(device),str(value),str(data['devices'][device][value]))
        file.add_section('Rinor')
        file.set('Rinor','addressport',str(data['Rinor']['addressport']))
        for action in data['actions']:
           print data['actions'][action]
           file.add_section(str(action))
           for value in data['actions'][action]:
              file.set(str(action),str(value),str(data['actions'][action][value]))
        file.add_section('Other')
        for value in data['Other']:
           file.set('Other',str(value), str(data['Other'][value]))

        with open(scene_file, 'w') as fich:
           file.write(fich)
        fich.close
        
        self._log.info("Add new scene %s Sucessfully")


class Mscene():
   
### devices is a dictionnary with all device
##### device is a dictionnary with keys: name, id, address,techno, key_stat, op, value, filters
####### filters is a list with filter

### Conditions beetwen 2 devices need define how...

### Action_true is a list with all action in dictionnary form, dictionnary key is address,techno, command and value
### Action_false is same as Action_true but for else case

    def __init__(self,scene,xplmanager,devices,Actions,rinor,host,logfile):
       #initialise les variables global
       self.log = logfile
       self.number= "scene_%s" %scene['name']
       self.log_scene('info',"initialisation")
       self.file = scene['file']
       self.gcondition=self.condition_formulate(scene['condition'])
       self.myxpl=xplmanager
       self.senderscene = "domogik-scene%s.%s" %(scene['name'],host)
       self.senderplug = "domogik-scene.%s" %host
       self.gaction_true = {}
       self.gaction_false ={}
       self.log_scene('info',"Initialisation of actions")
       for action in Actions:
          self.log_scene('info',("scene %s: Initialisation de l'action %s" %(self.number,Actions[action])))
          if Actions[action]["type"] == 'Action True':
             print 'Gaction_true'
             self.gaction_true[action]=Actions[action]
          if  Actions[action]["type"] == 'Action False':
             print 'Gaction_false'
             self.gaction_false[action]=Actions[action]
          
       self.grinor= rinor
       self.devices = devices

       self.initstat='1' #this variable enable or desable the launch command as init
       self.devices_stat={}
       self.devices_test={}
       print 'initilisation des stats'
       print 'liste des devices: %s' %devices
       ### init stat and test dictionnaries
       for device in devices:
          print device
          self.devices_stat[device]=''
          self.devices_test[device]=''
       self.send_msg_plugin("Stop", 'None')

      
      ### creat a listerner for scene cmnd
       self.glistener = Listener(self.cmd_scene,self.myxpl,{'schema':'scene.basic','xpltype':'xpl-cmnd','number':self.number})

    def cmd_scene(self,message):
       print ('command for %s' %self.number)
       if message.type == "xpl-cmnd" and 'command' in message.data:
          if message.data['command']=='start':
             self.log_scene('info', "Start command receive")
             self.scene_start()
          elif message.data['command']=='stop':
             self.log_scene('info', "Stop command receive")
             self.scene_stop()
          elif message.data['command']=='delete':
             self.log_scene('info', "Delete command receive")
             self.scene_delete()

    def log_scene(self, type, datalog):
        if type == "error":
           self.log.error("%s : %s" %(self.number,datalog))
           print("Error %s : %s" %(self.number,datalog))
        else:
           self.log.info("%s : %s" %(self.number,datalog))
           print("INFO %s : %s" %(self.number,datalog))

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
       self.log_scene('info', "Send and xpl message: %s" %msg)

    def get_stat(self):
### get last stat for a device, argument need is a device_id and the device_keystat
       for device in self.devices:
          the_url = 'http://%s/stats/%s/%s/latest' %(self.grinor, self.devices[device]['id'], self.devices[device]['key'])
          print 'the_url is: %s' %the_url
          req = urllib2.Request(the_url)
          handle = urllib2.urlopen(req)
          resp = handle.read()
          if len(ast.literal_eval(resp)['stats'])>0:
              self.devices_stat[device]= ast.literal_eval(resp)['stats'][0]['value']
          else:
              self.devices_stat[device] =""

    def start_listerner(self):
       self.listener = {}
       liste = 1
       for device in self.devices:
          if str(type(self.devices[device]['filters']))=="<type 'list'>":
             self.devices[device]['filters']=str(self.devices[device]['filters'])
          for i in range(len(eval(self.devices[device]['filters']))):
###todo add more data to filter like another key and a value for RFXcom for exemple
             if 'filter_key' in eval(self.devices[device]['filters'])[i]:
                 filte_string= "{'schema':"+ eval(self.devices[device]['filters'])[i]['schema']+",'xpltype':'xpl-trig',"+eval(self.devices[device]['filters'])[i]['device']+":"+self.devices[device]['adr']+","+ eval(self.devices[device]['filter_key'])[i]['device']+":"+eval(self.devices[device]['filter_value'])[i]['device']+"}"

                 self.listener[liste]=Listener(self.cmd_device,self.myxpl,{'schema':eval(self.devices[device]['filters'])[i]['schema'],'xpltype':'xpl-trig',eval(self.devices[device]['filters'])[i]['device']:self.devices[device]['adr'],eval(self.devices[device]['filter_key'])[i]['device']:eval(self.devices[device]['filter_value'])[i]['device']})
             else:
                 self.listener[liste]=Listener(self.cmd_device,self.myxpl,{'schema':eval(self.devices[device]['filters'])[i]['schema'],'xpltype':'xpl-trig',eval(self.devices[device]['filters'])[i]['device']:self.devices[device]['adr']})
             liste= liste+1
       self.log_scene("info","All listener start")

    def scene_start(self):
###initialise all device_stat et les listerners
       self.initstat='1'
       self.get_stat()
       self.start_listerner()
       self.send_msg_plugin('start', 'None')
       self.device_test()
       self.log_scene('info','Start done')
 
    def scene_delete(self):
### stop device listerner and del scene listerner
        self.scene_stop()
        try:
           os.remove(self.file)
        except:
           self.log_scene('error',"Can't remove file: %s" %self.file)
           
    def scene_stop(self):
### del all devices listerner
       for element in self.listener:
          print self.listener[element]
          self.myxpl.del_listener(self.listener[element])
       self.listener = {}
       self.send_msg_plugin('stop','None')
       self.log_scene('info','Stop done')

    def cmd_device(self, message):
### get the stat of message and place it in devices_stat
       self.log_scene('info', "Intercept an xpl-trig message: %s" %message)
       for device in self.devices:
           print device
           print self.devices[device]['key']
           print eval(self.devices[device]['filters'])[0]['xpl_stat']
           
           if self.devices[device]['key'] in message.data:
              print 'find key'
           for i in range(len(eval(self.devices[device]['filters']))):
              if eval(self.devices[device]['filters'])[0]['xpl_stat'] in message.data and eval(self.devices[device]['filters'])[i]['device'] in message.data:
                 if message.data[eval(self.devices[device]['filters'])[i]['device']]==self.devices[device]['adr']:
                    self.devices_stat[device]=message.data[eval(self.devices[device]['filters'])[0]['xpl_stat']]
       self.device_test()

    def send_command(self, actions):
### send to rinor all actions define in 'actions'
       print ("type de action:%s" %type(actions))
       if self.initstat != '1':
          for action in actions:
             if actions[action]['techno'] == 'command' and actions[action]['address']== 'command' and actions[action]['command']=='command':
                subp = subprocess.Popen(actions[action]['value'], shell=True)
             elif actions[action]['techno'] == 'send-xpl':
                self.send_action_xpl(actions[action])
             elif actions[action]['techno'] == 'Wait':
                self.wait_action(action['value'])
             else:
                self.rinor_command(actions[action])
       else:
          print ('1 test pour rien')
          self.initstat = 0

    def wait_action(self, time):
        time.sleep(time)
      
    def send_action_xpl(self, action):
### Send an xpl message define in scene action
     ### action['type_message'] =xpl-type
     ### action['schema'] = xpl schema
     ### action['value'] = xpl val
       msg=XplMessage()
       msg.set_source(self.senderscene)
       msg.set_schema(action['schema'])
       msg.set_type(action['type_message'])
#       if "Eval" in action['value'] or "eval" in action['value']:
#          msg.add_data(eval(action['value'].replace('Eval','')))
#       else:
#          msg.add_data(action['value'])
       msg.add_data(action['value'])
       self.myxpl.send(msg)

    def rinor_command(self,action):
### send rinot action

        if "Eval" in action['value'] or "eval" in action['value']:
           command_value = eval(action['value'].replace('Eval',''))
        else:
           command_value = action['value']

        if action['command']=='':
           the_url = 'http://%s/command/%s/%s/%s' %(self.grinor, action['techno'], action['address'], command_value)
        else:

           if action['value']=='':
              the_url = 'http://%s/command/%s/%s/%s' %(self.grinor,action['techno'], action['address'], action['command'])
           else:
              the_url = 'http://%s/command/%s/%s/%s/%s' %(self.grinor,action['techno'], action['address'], action['command'],command_value)
        req = urllib2.Request(the_url)
        handle = urllib2.urlopen(req)
        resp1 = handle.read()


    def device_test(self):
### test devices value and evaluate result
        print('test of device')
        print("value du message")

        for device in self.devices:
           if self.devices[device]['op'] != '':
              if self.devices[device]['op'] == '=':
                 if self.devices_stat[device].lower() == self.devices[device]['value'].lower():
                    self.devices_test[device]= True
                 else:
                    self.devices_test[device]= False
              elif self.devices[device]['op'] == '>':
                 if self.devices_stat[device] > self.devices[device]['value']:
                    self.devices_test[device]= True
                 else:
                    self.devices_test[device]= False
              elif self.devices[device]['op'] == '<':
                 if self.devices_stat[device] < self.devices[device]['value']:
                    self.devices_test[device]= True         
                 else:
                    self.devices_test[device]= False
           else:
              self.devices_test[device]=self.devices_stat[device]

        last_value=self.gcondition
        print 'conditon: %s' %self.gcondition
        print 'self.devices_test: %s' %self.devices_test
        print 'self.devices_stat: %s' %self.devices_stat

        try:
           new_value = eval(self.gcondition)
           self.log_scene('info',"new value: %s" %new_value)
        except:
           self.log_scene("error","incorrect Condition = %s" %self.gcondition)

        if last_value != new_value:
           if new_value == True:
              ### send command and xpl-trig
              self.send_msg_scene('xpl-trig', 'start','True')
              print("xpl-trig and gaction:%s" %self.gaction_true)
              self.send_command(self.gaction_true)
           if new_value == False:
              ### send command and xpl-trig
              self.send_msg_scene('xpl-trig', 'start','False')
              print("xpl-trig and gaction:%s" %self.gaction_false)
              self.send_command(self.gaction_false)
        else:
           if new_value == True:
              ### send xpl-stat
              self.send_msg_scene('xpl-stat', 'start','True')
              print("xpl-stat")
           if new_value == False:
              ### send xpl-stat
              print("xpl-stat")
              self.send_msg_scene('xpl-stat', 'start','False')

    def condition_formulate(self,condition):
### correction of condition test to do a correct test
       self.log_scene('info',"Condition = %s" %condition)
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
          device_ap = "self.devices_test['device%s'] " %i
          condition = condition.replace(device_av, device_ap)

       condition = " ".join(condition.split())
       self.log_scene('info',"new condition is = %s" %condition)

       return condition
