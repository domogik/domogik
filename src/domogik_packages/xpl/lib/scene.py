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
    number='0'
    device1 =''
    device2 =''
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
   
    def __init__(self,number,xplmanager,device1,device2,condition,Action_true,Action_false,rinor,host):
      print "number = %s" %number
      self.number="scene_%s" %number
      self.myxpl=xplmanager
      print "myxpl=%s" %self.myxpl
      self.senderscene = "domogik-scene%s.%s" %(number,host)
      self.senderplug = "domogik-scene.%s" %host  
      msg1=XplMessage()
      msg1.set_schema('scene.basic')
      msg1.set_source(self.senderplug)
      msg1.set_type('xpl-trig')
      msg1.add_data({'number': self.number})
      msg1.add_data({'run':'init'})
      msg1.add_data({'statue':'unknow'})
      self.myxpl.send(msg1)
      print "fin de l'init lib envoie du XPl"
#      XplPlugin.__init__(self, name = 'send', daemonize = False, parser = None, nohub = True)

     # number is the ref of the scene
     # device1 and 2 are dictionnary where found {address, id, key_stat, listener:[{schema,device field}]}
     # condition is dicationnary where can found {test1, value1, test2,value2, test_global}
     # Action_true and false are dictionnary where found {id, command, value}
     # rinor is a string 'rinor_ip:port'

      #initialise les variables global
      self.device2=device2
      self.device1=device1
      self.gaction_true=Action_true
      self.gaction_false=Action_false
      self.gcondition=condition
      self.grinor= rinor

      self.glistener = Listener(self.cmd_scene,self.myxpl,{'schema':'scene.basic','xpltype':'xpl-cmnd','number':self.number})

    def cmd_scene(self,message):
       print "reception d'un message scene: '%s'" %message
       print "command = %s" %message.data['command']
       if message.type == "xpl-cmnd":
          if message.data['command']=='start':
             self.start()
          elif message.data['command']=='stop':
             self.stop()

    def start(self):
       print 'start'
       print self.device1
       self.key_stat1 = self.device1['key_stat']

       if self.device2['id'] != '':
          print("device 2 id: %s") %self.device2['id']
          self.key_stat2 = self.device2['key_stat']

      #initialise les device_stat1 et 2 via un rinor et cree les listeners referant a cmd_device1 et cmd_device2

       the_url = 'http://%s/stats/%s/%s/latest' %(self.grinor, self.device1['id'], self.device1['key_stat'])
       print the_url
       req = urllib2.Request(the_url)
       handle = urllib2.urlopen(req)
       resp1 = handle.read()
       print resp1
       self.device1_stat= ast.literal_eval(resp1)['stats'][0]['value']
       print "stat device 1 : %s" %self.device1_stat
       self.listener1 = ['','','','','','','','','','']
       for i in range(len(self.device1['listener'])):
          self.listener1[i] = Listener(self.cmd_device1,self.myxpl,{'schema':self.device1['listener'][i]['schema'],'xpltype':'xpl-trig',self.device1['listener'][i]['device']:self.device1['address']})
          print("listener(self.cmd_device1,self.myxpl,{'schema':%s,'xpltype':xpl-trig, %s : %s") %(self.device1['listener'][i]['schema'],self.device1['listener'][i]['device'],self.device1['address'])
       if self.device2["id"] != '' and self.device2["key_stat"] != '':
          the_url = 'http://%s/stats/%s/%s/latest' %(self.grinor,self.device2['id'], self.device2['key_stat'])
          req = urllib2.Request(the_url)
          handle = urllib2.urlopen(req)
          resp2 = handle.read()
          self.device2_stat= ast.literal_eval(resp2)['stats'][0]['value']
          print "stat device 2 : %s" %self.device2_stat
          self.listener2 = ['','','','','','','','','','']
          for i in range(len(self.device2['listener'])):
             self.listener2[i]=Listener(self.cmd_device2,self.myxpl,{'schema':self.device2['listener'][i]['schema'],'xpltype':'xpl-trig',self.device2['listener'][i]['device']:self.device2['address']})
       msg1=XplMessage()
       msg1.set_source(self.senderplug)
       msg1.set_schema('scene.basic')
       msg1.set_type('xpl-trig')
       msg1.add_data({'number': self.number})
       msg1.add_data({'run':'start'})
       msg1.add_data({'stats':'None'})
       self.myxpl.send(msg1)

       self.etat_scene = self.test()
       

    def stop(self):
       for j in range(len(self.listener1)):
          if self.listener1[j] != '':
             self.myxpl.del_listener(self.listener1[j])
          if self.listener2[j] != '':
             self.myxpl.del_listener(self.listener2[j])
       msg1=XplMessage()
       msg1.set_schema('scene.basic')
       msg1.set_source(self.senderplug)
       msg1.set_type('xpl-trig')
       msg1.add_data({'number': self.number})
       msg1.add_data({'run':'stop'})
       msg1.add_data({'stats':'None'})
       self.myxpl.send(msg1)

    def cmd_device1(self, message):
       print "%s message for device1" %self.number
       for i in self.device1['listener']:
           print i
           if i['xpl_stat'] in message.data:
               print "%s message for device1" %self.number
               self.device1_stat=message.data[i['xpl_stat']]
               print 'new value for device 1 = %s' %self.device1_stat
               self.etat_scene = self.test()

    def cmd_device2(self, message):
       print "%s message for device2" %self.number
       for i in self.device2['listener']:
           print i
           if i['xpl_stat'] in message.data:
               self.device2_stat=message.data[i['xpl_stat']]
               print 'new value for device 2 = %s' %self.device2_stat
               self.etat_scene = self.test()


    def test(self):
       # function was call when an xpl-trig for on of device was receve
       last_value = self.etat_scene
       condition = 'none'
       condition1= 'none'
       condition2= 'none'
       print 'condition test device1 %s %s' %(self.gcondition['test1'],self.gcondition['value1'])
       if self.gcondition['test1'] != '' and self.gcondition['value1'] != '' :
          if self.gcondition['test1']=='=':
             if self.device1_stat == self.gcondition['value1']:
                condition1='true'
             else:
                condition1='false'
          elif self.gcondition['test1']=='<':
             print 'Test <'
             print self.gcondition['value1']
             print self.device1_stat
             if float(self.device1_stat) < float(self.gcondition['value1']):
                condition1='true'
             else:
                condition1='false'
          elif self.gcondition['test1']=='>':
             print 'test >'
             print 'condition:%s' %self.gcondition['value1']
             print 'stat:%s' %self.device1_stat
             print '%s > %s' %(self.device1_stat,self.gcondition['value1'])
             if float(self.device1_stat) > float(self.gcondition['value1']):
                condition1='true'
             else:
                condition1='false'
          elif self.gcondition['test1']=='!=':
             if self.device1_stat != self.gcondition['value1']:
                condition1='true'
             else:
                condition1='false'
       print "condition1:%s" %condition1

       print 'condition test device2 %s %s' %(self.gcondition['test2'],self.gcondition['value2'])
       if self.gcondition['test2'] != '' and self.gcondition['value2'] != '' :
          if self.gcondition['test2']== '=':
             if self.device2_stat == self.gcondition['value2']:
                condition2='true'
             else:
                condition2='false'
          elif self.gcondition['test2']== '<':
             if float(self.device2_stat) < float(self.gcondition['value2']):
                condition2='true'
             else:
                condition2='false'
          elif self.gcondition['test2']== '>':
             if float(self.device2_stat) > float(self.gcondition['value2']):
                condition2='true'
             else:
                condition2='false'
          elif self.gcondition['test2']== '!=':
             if self.device2_stat != self.gcondition['value2']:
                condition2='true'
             else:
                condition2='false'
       print "condition2 : %s" %condition2
       print "Global test %s" %self.gcondition['test_global']
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
             if float(self.device1_stat) > float(self.device2_stat):
                condition = 'true'
             else:
                condition = 'false'
          elif self.gcondition['test_global']== '!=':
             if self.device1_stat !=  self.device2_stat:
                condition2 = 'true'
             else:
                condition2 = 'false'
          elif self.gcondition['test_global']== 'And':
             if condition1 == 'true' and condition2 == 'true':
                condition = 'true'
             else:
                condition = 'false'
          elif self.gcondition['test_global']== 'Or':
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

       if condition == 'true' and condition != last_value and self.gaction_true != '':
          print ' envoie de la commande true'
#         http://ip:port/command/<technology>/<address>/<command>/command [/...]
          print 'techno: %s, address: %s,command: %s,value:%s' %(self.gaction_true['techno'], self.gaction_true['address'],self.gaction_true['command'], self.gaction_true['value'])

          if self.gaction_true['techno'] == 'command' and self.gaction_true['address']== 'command' and self.gaction_true['command']=='command':
             subp = subprocess.Popen(self.gaction_true['value'], shell=True) 

          if self.gaction_true['techno'] != '' and self.gaction_true['techno'] != 'command' and self.gaction_true['address'] != 'command':
             if self.gaction_true['command']=='':
                the_url = 'http://%s/command/%s/%s/%s' %(self.grinor, self.gaction_true['techno'], self.gaction_true['address'], self.gaction_true['value'])
             else:
              the_url = 'http://%s/command/%s/%s/%s/%s' %(self.grinor, self.gaction_true['techno'], self.gaction_true['address'], self.gaction_true['command'],self.gaction_true['value'])
             req = urllib2.Request(the_url)
             handle = urllib2.urlopen(req)
             resp1 = handle.read()
          msg=XplMessage()
          msg.set_source(self.senderscene)
          msg.set_schema('scene.basic')
          msg.set_type('xpl-trig')
          msg.add_data({'number': self.number})
          msg.add_data({'run':'start'})
          msg.add_data({'stats':'true'})
          self.myxpl.send(msg)

       if condition == 'false' and condition != last_value:
          print 'envoie de la commande false'

          if self.gaction_false['techno'] == 'command' and self.gaction_false['address']== 'command' and self.gaction_false['command']=='command':
             subp = subprocess.Popen(self.gaction_false['value'], shell=True) 

          if self.gaction_false['techno'] != '' and self.gaction_false['techno'] != 'command' and self.gaction_false['address'] != 'command':
             if self.gaction_false['command']== '':
                the_url = 'http://%s/command/%s/%s/%s' %(self.grinor, self.gaction_false['techno'], self.gaction_false['address'], self.gaction_false['value'])
             else:
                the_url = 'http://%s/command/%s/%s/%s/%s' %(self.grinor, self.gaction_false['techno'], self.gaction_false['address'], self.gaction_false['command'],self.gaction_false['value'])
             req = urllib2.Request(the_url)
             handle = urllib2.urlopen(req)
             resp1 = handle.read()
          msg=XplMessage()
          msg.set_source(self.senderscene)
          msg.set_schema('scene.basic')
          msg.set_type('xpl-trig')
          msg.add_data({'number': self.number})
          msg.add_data({'run':'start'})
          msg.add_data({'stats':'false'})
          self.myxpl.send(msg)
          print msg

       if condition == last_value:
          msg=XplMessage()
          msg.set_source(self.senderscene)
          msg.set_schema('scene.basic')
          msg.set_type('xpl-stat')
          msg.add_data({'number': self.number})
          msg.add_data({'run':'start'})
          msg.add_data({'stats': condition})
          self.myxpl.send(msg)

       return condition

def decode(message):
    """ dédage du message
    """
    print "%s" % message

if __name__ == "__main__":                                                      
                                                     
    obj = Scene(None, decode)
    obj.open()
    obj.listen()           


    
       


