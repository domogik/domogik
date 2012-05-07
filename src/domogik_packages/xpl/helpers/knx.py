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

Get informations about one wire network

Implements
==========

TODO

@author: Basilic <basilic3@htomail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.knx import KNXException
from domogik.xpl.lib.knx import KNX
from domogik.common.configloader import *
from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError



class KNXHelper(Helper):

   def __init__(self):
#      XplPlugin.__init__(momo, name ='knx')
#     momo._config = Query(self.myxpl, self.log)
      print "test"
      self.commands =   \
               { "all" : 
                  {
                    "cb" : self.all,
                    "desc" : "show all a devices on knx config file",
                    "usage" : "all"
                  },
               }

   def all(self, args=None):
      liste=[]
      filetoopen=XplPlugin.get_data_files_directory()
      filetoopen=filetoopen+'/knx.txt'
      fichier=open(filetoopen,"r")
      for ligne in fichier:
         liste.append(ligne)

      for i in range(len(liste)):
         print "%s. %s" %(i,liste[i])

MY_CLASS = {"cb": KNXHelper}
