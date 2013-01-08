#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import time
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.scene import *
from urllib import *
import ConfigParser
import glob
from xml.dom import minidom
import threading
import ast
import os

class SceneManager(XplPlugin):
   """Plugin destine a faire de petite automatisation
   """
   sceneCount = 0
   globalscene=[]
   def __init__(self):
      XplPlugin.__init__(self, name = 'scene')
      print ("manager= %s" %self.myxpl)
      self.manager= self.myxpl
      print (self.manager)
      
      try:
          self.scene = Scene(self.log, self.send_xpl)
          self.log.info("Start Scene")
          self.scene.open()

      except SceneException as err:
          self.log.error(err.value)
          print(err.value)
          self.force_leave()
          return

      ### Start listening 
      try:
          self.log.info("Start listening to Scene")
          scene_listen = threading.Thread(None,
                                        self.scene.listen,
                                        None,
                                        (),
                                        {})
          scene_listen.start()
      except SceneException as err:
          self.log.error(err.value)
          print(err.value)
          self.force_leave()
          return

      self.fake_stat = {}
      ### Create listeners for commands
      self.log.info("Creating listener for KNX")
      Listener(self.scene_cmd, self.myxpl,{'schema':'scene.basic'})
      self.enable_hbeat()
      
      self.SceneCount = self.init_file()

      all_scene = self.scene.read_all(self.path)
      
      for scene in all_scene:
         self.mem_scene(all_scene[scene])

      self.log.info("Plugin ready :)")

   def init_file(self):
### init the file system
       self.path = self.get_data_files_directory()
       initfile = self.path+'/init_scene.ini'      
       if os.path.exists(self.path) == False:
          os.mkdir(path, 0770)
       print os.path.isfile(initfile)
       if os.path.isfile(initfile) == False:
          file=ConfigParser.ConfigParser()
          file.add_section('Init')
          file.set('Init','number','0')
          number = 1
          with open(initfile, 'w') as fich:
             file.write(fich)
          fich.close
       else:
          file=ConfigParser.ConfigParser()
          file.read(initfile)
          number = file.get('Init','number')
       return number
      
   def mem_scene(self, scene):
### init scene one by one
      print(scene)
      devices={}
      actions={}
      for section in scene:
         if 'type' in scene[section]:
            if scene[section]['type']=='devices':
               devices[section]=scene[section]
            if scene[section]['type']=='Action True' or scene[section]['type']=='Action False':
               actions[section]=scene[section]
               
      Mini_scene = Mscene(scene['Scene'],self.manager,devices,actions,scene['Rinor']['addressport'],self.get_sanitized_hostname())

      if 'option_start' in scene:
         option_start=scene['option_start']
      else:
         option_start=True

      if option_start==True:
         Mini_scene.scene_start()

   def scene_cmd(self, message):
### function call when plugin receive a message
      if 'command' in message.data and 'data' in message.data:
         if message.data['command'] == 'Create':
            self.Create_scene_msg(message.data)
      if 'command' in message.data:
         print('command receive')
         if 'fake' in message.data['command']:
            print 'fake command'
            self.cmd_fake(message)

   def cmd_fake(self, message):
### sub send an answer for fake device of scene plugin
       if message.data['number'] not in self.fake_stat:
          self.fake_stat[message.data['number']]=''
       if message.data['command'] == "fake-true" or message.data['command'] == "fake-false" and message.type == "xpl-cmnd":
          print("Réception xpl cmnd")
          msg=XplMessage()
          msg.set_schema('scene.basic')
          sender= "domogik-scene0.%s" %self.get_sanitized_hostname()
          msg.set_source(sender)          
          if self.fake_stat[message.data['number']] != message.data['command']:
             msg.set_type('xpl-trig')
             self.fake_stat[message.data['number']] = message.data['command']
          else:
             msg.set_type('xpl-stat')   
          if message.data['command'] == "fake-true":
              msg.add_data({'stats': 'true'})
          if message.data['command'] == "fake-false":
              msg.add_data({'stats': 'false'})
          msg.add_data({'number': message.data['number']})
         
          self.myxpl.send(msg)
          
   def Create_scene_msg(self, data):
       devices = {}
       actions = {}
       data= data['data'].replace(':|',':{')
       data= data.replace('||','}}')
       data= data[1:-1]
       data= "{"+ data + "}"
       data= data.replace('|','}')

       data = ast.literal_eval(data)

       Scene_section = {'name':self.SceneCount}
       Scene_section['file'] = self.path+'/scene'+ str(self.SceneCount) + '.scn'
       Scene_section['description'] = 'description'
       Scene_section['condition'] = data['condition']
       print "ici la condition %s comme ça" %data['condition']
       for i in range(101):
          devices_text = "device" +str(i)
          if devices_text in data['devices']:
             device = {}
             device['type'] = 'devices'
             device['adr'] = data['devices'][devices_text]['adr']
             device['id'] = data['devices'][devices_text]['id']
             device['key'] = data['devices'][devices_text]['key']
             device['tech'] = data['devices'][devices_text]['tech']
             device['op']= data['devices'][devices_text]['op']
             device['value']= data['devices'][devices_text]['value']
             
             print "tech=%s and key=%s" %(device['tech'],device['key'])
             
             if device['tech'] != '' and device['key'] !='':
                device['filters'] = self.search_filter(device['tech'], device['key'])
                print 'device filter= %s' %device['filters']
                
             devices[devices_text]= device
          action_text = 'action'+str(i)
          if action_text in data['action']:
             action = {}
             action['type'] = data['action'][action_text]['type']
             action['address'] = data['action'][action_text]['address']
             action['command'] = data['action'][action_text]['command']
             if 'value' in data['action'][action_text]:
                action['value']= data['action'][action_text]['value']
             else:
                print('No value for this command')
                action['value']=''
             action['techno']= data['action'][action_text]['techno']
             actions[action_text]= action

       Rinor = {'addressport':data['rinor']}
       Other = {'run':data['start_run'], 'init_test':''}

       New_Scene = Mscene(Scene_section,self.manager,devices,actions,data['rinor'],self.get_sanitized_hostname())
       Scene_write={'Scene':Scene_section,'devices':devices,'actions':actions,'Rinor':Rinor,'Other':Other }
       self.scene.add_scene(Scene_write)
       self.send_xpl('scene_%s' %self.SceneCount)
       self.increase_scene()
       
       
      # print ('start_run:%s' %data['start_run'])
      # if data['start_run']=='true':
      #    New_Scene.scene_start()

   def increase_scene(self):
### Add 1 to the init file count scene
       self.SceneCount=int(self.SceneCount)+1
       print("add to init file")
       initfile = self.path+'/init_scene.ini'      
       file=ConfigParser.ConfigParser()
       file.add_section('Init')
       file.set('Init','number', self.SceneCount)
       with open(initfile, 'w') as fich:
          file.write(fich)
       fich.close
       print("that do")
       
   def send_xpl(self,data):
      print("send xpl...")
      msg=XplMessage()
      senderscene = "domogik-scene.%s" %self.get_sanitized_hostname()
      msg.set_source(senderscene)
      msg.set_schema('scene.basic')
      msg.set_type('xpl-trig')
      msg.add_data({'command': 'Create-ack'})
      msg.add_data({'scene': '0'})
      msg.add_data({'data':data})
      self.myxpl.send(msg)
      
### all function below this comment was copy to rest.py and adapte
   def search_filter(self, techno, key_stat):
### open all xml file to find xpl schema and parametrer for create correct listerner
      device_list=[]
      filetoopen= self.get_stats_files_directory()
      filetoopen= filetoopen[:filetoopen.find('stats')+6]
      files = glob.glob("%s/*/*xml" % filetoopen)
      res = {}
      for _files in files:
         print(_files)
         if _files[-4:] == ".xml":
            doc = minidom.parse(_files)
            technology = doc.documentElement.attributes.get("technology").value
#            print(technology)
            schema_types = self.get_schemas_and_types(doc.documentElement)
            if technology not in res:
               res[technology] = {}
            for schema in schema_types:
               #print(schema)
               if schema==schema:#schema not in res[technology]:
                  res[technology][schema] = {}
                  for xpl_type in schema_types[schema]:
                #     print(xpl_type)
                     if xpl_type == "xpl-trig" and technology == techno:
                        device, mapping, static_device, device_type = self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0])
                        for i in range(len(mapping)):
                           if "new_name" in mapping[i]:
                              if mapping[i]['new_name']==key_stat and schema not in device_list:
                                 test ={}
                                 test["schema"]="%s" %(schema)
                                 test["device"]="%s" %(device)
                                 test["xpl_stat"]="%s" %(mapping[i]['name'])
                                 device_list.append(test)
                           if mapping[i]['name']==key_stat and schema not in device_list:
                              test ={}
                              test["schema"]="%s" %(schema)
                              test["device"]="%s" %(device)
                              test["xpl_stat"]="%s" %(mapping[i]['name'])
                              device_list.append(test)
      return device_list

   def get_schemas_and_types(self, node):
      """ Get the schema and the xpl message type
      @param node : the root (statistic) node
      @return {'schema1': ['type1','type2'], 'schema2', ['type1','type3']}
      """
      res = {}
      schemas = node.getElementsByTagName("schema")
      for schema in schemas:
          res[schema.attributes.get("name").value] = {}
          for xpltype in schema.getElementsByTagName("xpltype"):
              if xpltype.attributes.get("type").value == "*":
                  res[schema.attributes.get("name").value]["xpl-trig"] = xpltype
                  res[schema.attributes.get("name").value]["xpl-stat"] = xpltype
              else:
                  res[schema.attributes.get("name").value][xpltype.attributes.get("type").value] = xpltype
      return res

   def parse_mapping(self, node):
      """ Parse the "mapping" node
      """

      values = []
      device_node = node.getElementsByTagName("device")[0]
      device = None
      static_device = None
      device_type = None
      if device_node.attributes.has_key("field"):
          device = device_node.attributes["field"].value.lower()
      elif device_node.attributes.has_key("static_name"):
          static_device = device_node.attributes["static_name"].value.lower()
      elif device_node.attributes.has_key("type"):
          device_type = device_node.attributes["type"].value.lower()

      for value in node.getElementsByTagName("value"):
          name = value.attributes["field"].value
          data = {}
          data["name"] = name
          #If a "name" attribute is defined, use it as vallue, else value is empty
          if value.attributes.has_key("history_size"):
              data["history_size"] = int(value.attributes["history_size"].value)
          else:
              data["history_size"] = 0
          if value.attributes.has_key("new_name"):
              data["new_name"] = value.attributes["new_name"].value.lower()
              if value.attributes.has_key("filter_key"):
                  data["filter_key"] = value.attributes["filter_key"].value.lower()
                  if value.attributes.has_key("filter_value"):
                      data["filter_value"] = value.attributes["filter_value"].value.lower()
                  else:
                      data["filter_value"] = None
              else:
                  data["filter_key"] = None
                  data["filter_value"] = None
          else:
              data["new_name"] = None
              data["filter_key"] = None
              data["filter_value"] = None
          values.append(data)
      return device, values, static_device, device_type

if __name__ == "__main__":

   INST = SceneManager()
