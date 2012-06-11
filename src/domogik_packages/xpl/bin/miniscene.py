#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import time
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.miniscene import MiniScene


class MiniScene(XplPlugin):
   """Plugin destine a faire de petite automatisation
   """
   def __init__(self):
      XplPlugin.__init__(self, name = 'miniscene')
      self._config = Query(self.myxpl, self.log)
       # Configuration
      self._config = Query(self.myxpl, self.log)

      ### Create Mini_Scene object
      try:
          self.miniscene = MiniScene(self.log, self.send_xpl)
          self.log.info("Start Mini Scene")


      except MiniSceneException as err:
          self.log.error(err.value)
          print(err.value)
          self.force_leave()
          return

      ### Start listening 
      try:
          self.log.info("Start listening to Mini Scene")
          mini_scene_listen = threading.Thread(None,
                                        self.miniscene.listen,
                                        "listen_miniscene",
                                        (),
                                        {})
          miniscene_listen.start()
      except MiniSceneException as err:
          self.log.error(err.value)
          print(err.value)
          self.force_leave()
          return


      ### Create listeners for commands
      self.log.info("Creating listener for KNX")
      Listener(self.miniscene_cmd, self.myxpl,{'schema':'miniscene.basic'})
      self.add_stop_cb(self.miniscene.close)
      self.enable_hbeat()

      self.log.info("Plugin ready :)")

   def mini_scene_cmd(self, message):
      print "2"       

   def send_xpl(self,data):
       """boucle d'envoie d'une message xpl
       """


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

   INST = MiniScene()

