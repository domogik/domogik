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
      ### Create Mini_Scene object
      print "manager= %s" %self.myxpl
      self.manager= self.myxpl
      print self.manager
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


      ### Create listeners for commands
      self.log.info("Creating listener for KNX")
      Listener(self.scene_cmd, self.myxpl,{'schema':'scene.basic'})
      self.enable_hbeat()
      self.filetoopen=self.get_data_files_directory()
      path = self.get_data_files_directory()
      if os.path.exists(path)== False:
         os.mkdir(path)
         print "Création du répertoire %s" %path
      self.filetoopen= self.filetoopen+"/scene.txt"
      if os.path.exists(self.filetoopen)== False:
         fichier= open(self.filetoopen,'w')
         fichier.write('')
         fichier.close()
         print "Création du fichier de stockage %s" %self.filetoopen
      mem = self.scene.read_scene(self.filetoopen)

      self.sceneCount='0'
      for i in range(len(mem)):
         liste=str(mem[i])
         print "maliste:%s" %liste
         msg=XplMessage()
         msg.set_schema('scene.basic')
         msg.set_type('xpl-cmnd')
         if liste !='':
            liste=ast.literal_eval(liste)
            print liste
            self.mem_scene(liste) 
            for _truc in liste:
               print "%s : %s" %(_truc,liste[_truc])

      self.log.info("Plugin ready :)")

   def mem_scene(self, ligne):
   ### create a scene for init plugin
   ### msg="{'scene':'%s','device1':%s,'device2':%s,'condition':%s,'action_true':%s,'action_false':%s,'rinor':'%s'}\n" %(self.sceneC,device1,device2,condition,action_true,action_false,rinor)
      self.sceneCount = int(ligne['scene'])#self.sceneCount + 1
      Mini_scene = Mscene(ligne['scene'],self.manager,ligne['device1'],ligne['device2'],ligne['condition'],ligne['action_true'],ligne['action_false'],ligne['rinor'])
      Mini_scene.start()

   def scene_cmd(self, message):
      """ routine lorsque le plugin recoit un message xpl
      """
      if "data" in message.data:
          data = message.data['data']
          data = data.replace('|','')
          data = data.replace(':',":'")
          data = data.replace(',',"',")
          data = "{" + data + "'}"
          data = ast.literal_eval(data)
          print data 
      if message.data['command']=="Create" and message.data['scene'] =='0':
         msg=''
         self.sceneCount = self.sceneCount + 1
         if 'scene' not in data:
            self.sceneC = self.sceneCount
         else:
            self.sceneC = message
         device1_id = ''
         device1_adr = ''
         device1_tech = ''
         device1_key = ''
         device1_op = ''
         device1_value = ''
         device2_id = ''
         device2_adr = ''
         device2_tech = ''
         device2_key = ''
         device2_op = ''
         device2_value = ''
         op_global = ''
         action_true_techno = ''
         action_true_adr = ''
         action_true_value = ''
         action_true_cmd = ''
         action_false_techno = ''
         action_false_adr = ''
         action_false_value = ''
         action_false_cmd = ''
         filter_device1 = ''
         filter_device2 = ''

         rinor=data['rinorip']+":"+data['rinorport']
         print 'rinor:%s' %rinor

         if 'device1id' in data and data['device1id'] != '':
            device1_adr = data['device1adr']
            device1_id = data['device1id']
            device1_key = data['device1key']
            device1_tech= data['device1tech']
            device1_key= data['device1key']
            if 'device1op' in data and data['device1op'] != '':
               device1_op= data['device1op']
               device1_value= data['device1val']

         if 'device2id' in data and data['device2id'] != '':
            device2_adr = data['device2adr']
            device2_id = data['device2id']
            device2_key = data['device2key']
            device2_tech= data['device2tech']
            device2_key= data['device2key']
            if 'device2op' in data and data['device2op']!='':
               device2_op= data['device2op']
               device2_value= data['device2val']

         if 'opglobal' in data and data['opglobal'] != '':
            op_global = data['opglobal']

         condition={'test1':device1_op, 'value1':device1_value,'test2':device2_op,'value2':device2_value,'test_global':op_global}

         if 'actiontrueadr' in data and data['actiontrueadr'] != '':
            action_true_techno = data['actiontruetech']
            action_true_adr = data['actiontrueadr']
            action_true_value = data['actiontrueval']
            if 'actiontruecmd' in data:
                action_true_cmd = data['actiontruecmd']

         action_true={'techno':action_true_techno,'address':action_true_adr, 'command':action_true_cmd,'value':action_true_value}

         if 'actionfalseadr' in data and data['actionfalseadr'] != '':
            action_false_techno = data['actionfalsetech']
            action_false_adr = data['actionfalseadr']
            action_false_value = data['actionfalseval']
            if 'actionfalsecmd' in data:
                action_false_cmd = data['actionfalsecmd']

         action_false={'techno':action_false_techno,'address':action_false_adr, 'command':action_false_cmd,'value':action_false_value}
         
         if device1_tech != '' and device1_key !='':
            filter_device1 = self.search_filter(device1_tech, device1_key)
            print "filre: %s" %filter_device1
         if device2_tech != '' and device2_key != '':
            filter_device2 = self.search_filter(device2_tech, device2_key)

         device1 = {'address':device1_adr,'id':device1_id, 'key_stat':device1_key,'listener':filter_device1}
         device2 = {'address':device2_adr,'id':device2_id, 'key_stat':device2_key,'listener':filter_device2}
         
         print 'self.manager=%s' %self.manager
         Mini_scene = Mscene(self.sceneC,self.manager,device1,device2,condition,action_true,action_false, rinor)
         msg="{'scene':'%s','device1':%s,'device2':%s,'condition':%s,'action_true':%s,'action_false':%s,'rinor':'%s'}\n" %(self.sceneC,device1,device2,condition,action_true,action_false,rinor)
         self.scene.add_scene(self.filetoopen,msg)

#         the_url="http://%s/base/device/add/name/%s/address/%s/usage_id/scene/description/scene_plugin/reference/Mscene" %(self.Mscene,self.Mscene)

         Mini_scene.start()

         print "création d'une scene"
         msg=XplMessage()
         msg.set_schema('scene.basic')
         msg.set_type('xpl-trig')
         msg.add_data({'command':'Create-ack'})
         msg.add_data({'scene':'0'})
         scene_number= 'scene_%s OK' %self.sceneC
         msg.add_data({'data':scene_number}) 

         self.myxpl.send(msg)

      elif message.data['command']=="start":
         print 'Start scene'
      elif message.data['command']=='stop':
         print 'Stop scene'

   def send_xpl(self,data):
       """boucle d'envoie d'une message xpl
       """
       print "send_xpl"

   def search_filter(self, techno, key_stat):
      device_list=[]
      filetoopen= self.get_stats_files_directory()
      filetoopen= filetoopen[:filetoopen.find('stats')+6]
      files = glob.glob("%s/*/*xml" % filetoopen)
      print "files récupérer"
      res = {}
      print "technologie: %s, key_stat: %s" %(techno,key_stat)
      for _files in files:
         if _files[-4:] == ".xml":
            doc = minidom.parse(_files)
            technology = doc.documentElement.attributes.get("technology").value
            schema_types = self.get_schemas_and_types(doc.documentElement)
            if technology not in res:
               res[technology] = {}
            for schema in schema_types:
               if schema not in res[technology]:
                  res[technology][schema] = {}
                  for xpl_type in schema_types[schema]:
                     if xpl_type == "xpl-trig" and technology == techno:
                        device, mapping, static_device, device_type = self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0])
                        print "device: %s" %device
                        for i in range(len(mapping)):
                           print "keystat recherche %s, schema %s" %(mapping[i]['name'], schema)
                           print "mapping= %s" %mapping[i]
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
      print "device_list: %s" %device_list
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
