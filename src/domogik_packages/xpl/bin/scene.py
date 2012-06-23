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

class SceneManager(XplPlugin):
   """Plugin destine a faire de petite automatisation
   """
   def __init__(self):
      XplPlugin.__init__(self, name = 'scene')
       # Configuration
#      self._config = Query(self.myxpl, self.log)
 #     print self._config
      ### Create Mini_Scene object
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

      self.log.info("Plugin ready :)")

   def scene_cmd(self, message):
      """ routine lorsque le plugin recoit un message xpl
      """
      print "scene_cmd"       

   def send_xpl(self,data):
       """boucle d'envoie d'une message xpl
       """
       print "send_xpl"

   def search_filter(self, techno, device_adr, key_stat):

      filetoopen= self.get_stats_files_directory()
      filetoopen= filetoopen[:filetoopen.find('stats')+6]
      files = glob.glob("%s/*/*xml" % filetoopen)
      print "files récupérer"
      res = {}
      for _files in files:
         if _files[-4:] == ".xml":
            doc = minidom.parse(_files)
            technology = doc.documentElement.attributes.get("technology").value
            schema_types = self.get_schemas_and_types(doc.documentElement)
            if technology not in res:
               res[technology] = {}
            device_list=[]
            for schema in schema_types:
               if schema not in res[technology]:
                  res[technology][schema] = {}
               for xpl_type in schema_types[schema]:
                   if xpl_type == "xpl-trig" and technology == techno:
                      device, mapping, static_device, device_type = self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0])
                      if len(filter(str(device),device_list)) == 0:
                         print "test reussi"
                         device_list.append(str(device))

                   print str(device_list)
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



   def create_scene(num_script, rest_server, id_device1, key_stat1, test1, value1, id_device2, key_stat2, test2, value2,technologie1, adress_1,value_out1,technologie2,adress_2, value_out2, test_type, temp_wait):

      filetoopen = "mini_scene%s.py" %num_script
      fichier = open(filetoopen,"a")

      fichier.write("#!/usr/bin/python  \n \n")

      fichier.write("import urllib2  \n")

      fichier.write("import time  \n \n")

      fichier.write("while True:  \n")
   
      url = "   the_url = 'http://%s/stats/%s/%s/latest' \n" %(rest_server, id_device1, key_stat1)
      fichier.write(url)
      fichier.write("   req = urllib2.Request(the_url)  \n")
      fichier.write("   handle = urllib2.urlopen(req)  \n")
      fichier.write("   resp1 = handle.read()  \n")
      fichier.write("   resp1 = resp1[resp1.find('value')+10:]  \n")
      fichier.write("   resp1 = resp1[:resp1.find(',')-1]  \n")
      if test1 != "==" and test1 != "":
         fichier.write("   resp1 = float(resp1)\n")

      if id_device2<>"":
         url = "   the_url = 'http://%s/stats/%s/%s/latest' \n" %(rest_server, id_device2, key_stat2)
         fichier.write(url)
         fichier.write("   req = urllib2.Request(the_url)  \n")
         fichier.write("   handle = urllib2.urlopen(req)  \n")
         fichier.write("   resp2 = handle.read()  \n")
         fichier.write("   resp2 = resp2[resp2.find('value')+10:]  \n")
         fichier.write("   resp2 = resp2[:resp2.find(',')-1]  \n")
         if test2 != "==" and test2 != "":
            fichier.write("   resp2 = float(resp2)\n")

         if test_type != "and" and test_type != "or":
            fichier.write("   resp1 = float(resp1)\n")
            fichier.write("   resp2 = float(resp2)\n")


      condition = "   if resp1 %s%s: \n" %(test1, value1)
      if id_device2 != "" and test_type != "":
         condition = '   if resp1 %s%s %s resp2 %s%s : \n' %(test1, value1,test_type,test2,value2)

      fichier.write(condition)

      if technologie1 != "":
         si_vrai="      the_url = 'http://%s/command/%s/%s/%s' \n" %(rest_server, technologie1, adress_1, value_out1)
         si_vrai=si_vrai.replace('"','')
         fichier.write(si_vrai)
         fichier.write("      req = urllib2.Request(the_url)  \n")
         fichier.write("      handle = urllib2.urlopen(req)  \n")
         fichier.write("      cmd1 = handle.read()  \n")

      if technologie2 != "":
         fichier.write("   else:\n")
         si_vrai="      the_url = 'http://%s/command/%s/%s/%s' \n" %(rest_server, technologie2, adress_2, value_out2)
         si_vrai=si_vrai.replace('"','')
         fichier.write(si_vrai)
         fichier.write("      req = urllib2.Request(the_url)  \n")
         fichier.write("      handle = urllib2.urlopen(req)  \n")
         fichier.write("      cmd1 = handle.read()  \n")
   
      tempo = "   time.sleep(%s)" %temp_wait
      fichier.write(tempo)
      fichier.close
      command = "chmod +x mini_scene%s.py" %num_script
      subp2 = subprocess.Popen(command, shell = True)
      command = "python mini_scene%s.py" %num_script
      subp2 = subprocess.Popen(command, shell = True)
      print "Mini Scene Lancer"

   def start_scene(num_script):
      command = "python mini_scene%s.py" %num_script
      subp2 = subprocess.Popen(command, shell = True)

if __name__ == "__main__":

   INST = SceneManager()
