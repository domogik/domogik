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

Library to simply manager plugin's xml file description

Implements
==========

PackageXml

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.configloader import Loader
from xml.dom import minidom
import traceback


PLG_XML_PATH = "share/domogik/plugins/"

class PackageException(Exception):
    """
    Package exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class PackageXml():
    def __init__(self, name = None, url = None, path = None):
        """ Read xml file of a plugin and make an object from it
            @param name : name of plugin
            @param url : url of xml file
            @param path : path of xml file
        """
        xml_file = None
        try:
            if name != None:
                # get config
                cfg = Loader('domogik')
                config = cfg.load()
                conf = dict(config[1])

                xml_plugin_directory = "%s/%s" % (conf['custom_prefix'], PLG_XML_PATH)
                xml_file = "%s/%s.xml" % (xml_plugin_directory, name)
                self.info_file = xml_file
                self.xml_content = minidom.parse(xml_file)
    
            if path != None:
                xml_file = path
                self.info_file = xml_file
                self.xml_content = minidom.parse(xml_file)

            if url != None:
                xml_file = url
                self.info_file = xml_file
                xml_data = urllib.urlopen(xml_file)
                self.xml_content = minidom.parseString(xml_data.read())

            # read xml file
            self.type = self.xml_content.getElementsByTagName("package")[0].attributes.get("type").value
            self.name = self.xml_content.getElementsByTagName("name")[0].firstChild.nodeValue
            self.desc = self.xml_content.getElementsByTagName("description")[0].firstChild.nodeValue
            self.detail = self.xml_content.getElementsByTagName("detail")[0].firstChild.nodeValue
            self.techno = self.xml_content.getElementsByTagName("technology")[0].firstChild.nodeValue
            self.version = self.xml_content.getElementsByTagName("version")[0].firstChild.nodeValue
            self.doc = self.xml_content.getElementsByTagName("documentation")[0].firstChild.nodeValue
            self.author = self.xml_content.getElementsByTagName("author")[0].firstChild.nodeValue
            self.email = self.xml_content.getElementsByTagName("author-email")[0].firstChild.nodeValue
            # list of files
            self.files = []
            xml_data = self.xml_content.getElementsByTagName("files")[0]
            for my_file in xml_data.getElementsByTagName("file"):
               data = {"path" :  my_file.attributes.get("path").value}
               self.files.append(data)
            # list of depandancies
            self.depandancies = []
            xml_data = self.xml_content.getElementsByTagName("depandancies")[0]
            for dep in xml_data.getElementsByTagName("dep"):
               data = {"name" :  dep.attributes.get("name").value}
               self.depandancies.append(data)

            # construct filenames
            self.fullname = "%s-%s" % (self.type, self.name)
            self.xml_filename = "%s-%s-%s.xml" % (self.type, self.name, self.version)
            self.pkg_filename = "%s-%s-%s.tar.gz" % (self.type, self.name, self.version)

            # repository specifics
            rep = self.xml_content.getElementsByTagName("repository")
            if len(rep) == 0:
                self.package_url = None
                self.xml_url = None
                self.priority = None
            else:
                url_prefix = rep[0].attributes.get("url_prefix").value
                self.package_url = "%s.tar.gz" % url_prefix
                self.xml_url = "%s.xml" % url_prefix
                self.priority = rep[0].attributes.get("priority").value

        except:
            raise PackageException("Error reading xml file : %s : %s" % (xml_file, str(traceback.format_exc())))


    def cache_package(self, cache_folder, url_prefix, priority):
        """ Add url_prefix info in xml data
            Store xml in a file in cache_folder
            @param cache_folder : folder to put xml file
            @param url_prefix : http://.../pluginname-version
            @param priority : repository priority
        """
        top_elt = self.xml_content.documentElement
        new_elt = self.xml_content.createElementNS(None, 'repository')
        new_elt.setAttribute("url_prefix", url_prefix)
        new_elt.setAttribute("priority", priority)
        top_elt.appendChild(new_elt)
        cache_file = open("%s/%s" % (cache_folder, self.xml_filename), "w") 
        cache_file.write(self.xml_content.toxml().encode("utf-8"))
        cache_file.close()

    def display(self):
        """ Display xml data in a fine way
        """
        print("---- Plugin informations --------------------------------")
        print("Type           : %s" % self.type)
        print("Name           : %s" % self.name)
        print("Full name      : %s" % self.fullname)
        print("Version        : %s" % self.version)
        print("Technology     : %s" % self.techno)
        print("Link for doc   : %s" % self.doc)
        print("Description    : %s" % self.desc)
        print("Detail         : %s" % self.detail)
        print("Author         : %s" % self.author)
        print("Author's email : %s" % self.email)
        print("----- Plugin depandancies -------------------------------")
        for dep in self.depandancies:
            print("- %s" % dep["name"])
        print("----- Plugin files --------------------------------------")
        for my_file in self.files:
            print("- %s" % my_file["path"])
        if self.package_url != None:
            print("----- Repository informations ---------------------------")
            print("Package path   : %s" % self.package_url)
            print("Xml path       : %s" % self.xml_url)
            print("Priority       : %s" % self.priority)
        print("---------------------------------------------------------")


