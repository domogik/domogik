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

Package manager for domogik
A package could be a plugin, a web ui widget, etc

Implements
==========

TODO

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.configloader import Loader
from optparse import OptionParser
from xml.dom import minidom
import traceback
import tarfile
import tempfile
import os
from subprocess import Popen
import urllib
from operator import attrgetter


PACKAGE_TYPES = ['plugin']
SRC_PATH = "../../../"
PLG_XML_PATH = "src/share/domogik/plugins/"
SETUP_PLUGIN_TPL = "./templates/setup-plugin.tpl"
TMP_EXTRACT_DIR = "domogik-pkg-mgr" # used with /tmp (or assimilated) before
REPO_SRC_FILE = "/etc/domogik/sources.list"
REPO_LST_FILE = "packages.lst"

class PackageException(Exception):
    """
    Package exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class PackageManager():
    """ Tool to create packages
    """

    def __init__(self):
        """ Init tool
        """

        # Options management
        usage = "usage: %prog [options] <plugin name>"
        parser = OptionParser(usage = usage)
        parser.add_option("-c", "--create",
                          action = "store_true", 
                          dest = "action_create",
                          default = False,
                          help = "Create a new package")
        parser.add_option("-f", "--force",
                          action = "store_true", 
                          dest = "force",
                          default = False,
                          help = "Script won't ask user to continue or not")
        parser.add_option("-i", "--install",
                          action = "store_true", 
                          dest = "action_install",
                          default = False,
                          help = "Install a package")
        parser.add_option("-u", "--update",
                          action = "store_true", 
                          dest = "action_update",
                          default = False,
                          help = "Update packages list")
        parser.add_option("-t", "--type",
                          action = "store", 
                          dest = "package_type",
                          help = "Package type : %s" % PACKAGE_TYPES)
        parser.add_option("-o", "--output-dir",
                          action = "store", 
                          dest = "output_dir",
                          help = "Directory where you want to create packages")

        (self.options, self.args) = parser.parse_args()

        # check args
        if self.options.action_update == False and len(self.args) != 1:
            print("Error : missing argument : plugin name")
            return
  
        # package creation
        if self.options.action_create == True:
            # check package type
            if self.options.package_type not in PACKAGE_TYPES:
                print("Error : : type must be in this list : %s" % PACKAGE_TYPES)
                return

            # plugin
            if self.options.package_type == "plugin":
                self._create_package_for_plugin(self.args[0], self.options.output_dir)

        # package installation
        if self.options.action_install == True:
            # check package type and -o
            if self.options.package_type != None:
                print("Error : --type should not be used with install option")
                return
            if self.options.output_dir != None:
                print("Error : --output-dir should not be used with install option")
                return

            # install
            self._install_package(self.args[0])

        # packages list update
        if self.options.action_update == True:
            # check package type and -o
            if self.options.package_type != None:
                print("Error : --type should not be used with install option")
                return
            if self.options.output_dir != None:
                print("Error : --output-dir should not be used with install option")
                return

            # update list
            self._update_list()
        

    def _create_package_for_plugin(self, name, output_dir):
        """ Create package for a plugin
            1. read xml file to get informations and list of files
            2. generate package
            @param name : name of plugin
        """
        print("Plugin nam : %s" % name)

        try:
            plg_xml = PluginXml(name)
        except:
            print(str(traceback.format_exc()))
            return
        print("Xml file OK")

        # display plugin informations
        print("---- Plugin informations --------------------------------")
        print("Name           : %s" % plg_xml.name)
        print("Version        : %s" % plg_xml.version)
        print("Technology     : %s" % plg_xml.techno)
        print("Link for doc   : %s" % plg_xml.doc)
        print("Description    : %s" % plg_xml.desc)
        print("Detail         : %s" % plg_xml.detail)
        print("Author         : %s" % plg_xml.author)
        print("Author's email : %s" % plg_xml.email)
        print("----- Plugin depandancies -------------------------------")
        for dep in plg_xml.depandancies:
            print("- %s" % dep["name"])
        print("----- Plugin files --------------------------------------")
        for my_file in plg_xml.files:
            print("- %s" % my_file["path"])
        print("---------------------------------------------------------")

        # check file existence
        if plg_xml.files == []:
            print("There is no file defined : the package won't be created")
            return

        if self.options.force == False:
            print("\nAre these informations OK ?")
            resp = raw_input("[o/N]")
            if resp.lower() != "o":
                print("Exiting...")
                return

        # Create setup.py file
        setup_file = self._create_plugin_setup(plg_xml)

        # Create .tar.gz
        self._create_tar_gz("plugin-%s-%s" % (plg_xml.name, plg_xml.version), 
                            output_dir,
                            plg_xml.files, 
                            plg_xml.info_file,
                            setup_file = setup_file,
                            ez_setup_file = SRC_PATH + "ez_setup.py")


    def _create_plugin_setup(self, plg_xml):
        """ Create setup.py file for package
            @param plg_xml : plugin data (from xml file)
        """
        output_path = "%s/setup_%s.py" % (tempfile.gettempdir(), plg_xml.name)
        print("Generating '%s'" % output_path)
        input_file = open(SETUP_PLUGIN_TPL, "r")

        data = ""
        for buf in input_file.readlines():
            data = data + buf 

        data = data.replace("%name%", plg_xml.name)
        data = data.replace("%version%", plg_xml.version)
        data = data.replace("%doc%", plg_xml.doc)
        data = data.replace("%desc%", plg_xml.desc)
        data = data.replace("%author%", plg_xml.author)
        data = data.replace("%email%", plg_xml.email)
        dep_list = ""
        for dep in plg_xml.depandancies:
            dep_list += "'%s'," % dep["name"]
        dep_list = dep_list[0:-1]
        data = data.replace("%depandancies%", dep_list)

        output_file = open(output_path, "w")
        output_file.write(data.encode("utf-8"))
        output_file.close()
 
        return output_path


    def _create_tar_gz(self, name, output_dir, files, info_file = None,
                       setup_file = None, ez_setup_file = None):
        """ Create a .tar.gz file anmmed <name.tgz> which contains <files>
            @param name : file name
            @param output_dir : if != None, the path to put .tar.gz
            @param files : table of file names to add in tar.gz
            @param info_file : path for info.xml file
            @param setup_file : path for setup.py file
            @param ez_setup_file : path for ez_setup.py file
        """
        if output_dir == None:
            my_tar = "%s/%s.tar.gz" % (tempfile.gettempdir(), name)
        else:
            my_tar = "%s/%s.tar.gz" % (output_dir, name)
        print("Generating package : '%s'" % my_tar)
        try:
            tar = tarfile.open(my_tar, "w:gz")
            for my_file in files:
                path =  str(my_file["path"])
                print("- %s" % path)
                tar.add(SRC_PATH + path, arcname = path)
            if info_file != None:
                print("- info.xml")
                tar.add(info_file, arcname="info.xml")
            if setup_file != None:
                print("- setup.py")
                tar.add(setup_file, arcname="setup.py")
            if ez_setup_file != None:
                print("- ez_setup.py")
                tar.add(ez_setup_file, arcname="ez_setup.py")
            tar.close()
        except: 
            raise PackageException("Error generating package : %s : %s" % (my_tar, traceback.format_exc()))
        print("OK")
    

    def _install_package(self, path):
        """ Install a package
            0. Eventually download package
            1. Extract tar.gz
            2. Launch ez_setup.py
            3. Launch setup install.py
            @param path : path for tar.gz
        """
        # get plugin name
        full_name = os.path.basename(path)
        # twice to remove first .gz and then .tar
        name =  os.path.splitext(full_name)[0]
        name =  os.path.splitext(name)[0] 
        print("Plugin name : %s" % name)

        # get temp dir to extract data
        my_tmp_dir_dl = "%s/%s" % (tempfile.gettempdir(), TMP_EXTRACT_DIR)
        my_tmp_dir = "%s/%s" % (my_tmp_dir_dl, name)
        print("Creating temporary directory : %s" % my_tmp_dir)
        try:
            if os.path.isdir(my_tmp_dir) == False:
                os.makedirs(my_tmp_dir)
        except:
            raise PackageException("Error while creating temporary folder '%s' : %s" % (my_tmp_dir, traceback.format_exc()))

        # Check if we need to download package
        if path[0:4] == "http":
            print("Downloading package : %s" % path)
            dl_path = "%s/%s" % (my_tmp_dir_dl, full_name)
            urllib.urlretrieve(path, dl_path)
            path = dl_path
            print("Package downloaded : %s" % path)

        # extract
        print("Extracting package...")
        try:
            self._extract_package(path, my_tmp_dir)
        except:
            raise PackageException("Error while extracting package '%s' : %s" % (path, traceback.format_exc()))
        print("Package successfully extracted.")


        print"TMP=%s" % my_tmp_dir

        # launch package installation
        print("Starting installation...")
        try:
            self._launch_setup_py(my_tmp_dir)
        except:
            raise PackageException("Error while installing package '%s' : %s" % (path, traceback.format_exc()))
        print("Package installation finished")


    def _extract_package(self, pkg_path, extract_path):
        """ Extract package <pkg_path> in <extract_path>
            @param pkg_path : path to package
            @param extract_path : path for extraction
        """
        tar = tarfile.open(pkg_path)
        # TODO : check if there is no .. or / in files path
        tar.extractall(path = extract_path)
        tar.close()


    def _launch_setup_py(self, path):
        """ Launch setup.py install in <path>
            @param path : path where is located setup.py
        """
        subp = Popen("/usr/bin/python setup.py install", 
                      cwd = path, 
                      shell = True)
        subp.wait()
        return subp.pid


    def _update_list(self):
        """ update local package list
        """
        print "update action"
        try:
            # Read repository source file and generate repositories list
            repo_list = self._get_repositories_list(REPO_SRC_FILE)
            print repo_list
        except:
            print(str(traceback.format_exc()))
            return
             
        # TODO : sort list
        print sorted(repo_list, key = attrgetter("priority"))

        # for each list, get files and associated xml


    def _get_repositories_list(self, filename):
        """ Read repository source file and return list
            @param filename : source file
        """
        try:
            repo_list = []
            src_file = open(filename, "r")
            for line in src_file.readlines():
                repo_list.append({"priority" : line.split()[0],
                                  "url" : line.split()[1]})
            src_file.close()
        except:
            raise PackageException("Error reading source file : %s : %s" % (REPO_SRC_FILE, str(traceback.format_exc())))
        return repo_list


class PluginXml():
    def __init__(self, name):
        """ Read xml file of a plugin and make an object from it
            @param name : name of plugin
        """
        # get config
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        xml_plugin_directory = "%s/%s" % (SRC_PATH, PLG_XML_PATH)
        xml_file = "%s/%s.xml" % (xml_plugin_directory, name)
        self.info_file = xml_file

        # read xml file
        try:
            xml_content = minidom.parse(xml_file)
            self.name = xml_content.getElementsByTagName("name")[0].firstChild.nodeValue
            self.desc = xml_content.getElementsByTagName("description")[0].firstChild.nodeValue
            self.detail = xml_content.getElementsByTagName("detail")[0].firstChild.nodeValue
            self.techno = xml_content.getElementsByTagName("technology")[0].firstChild.nodeValue
            self.version = xml_content.getElementsByTagName("version")[0].firstChild.nodeValue
            self.doc = xml_content.getElementsByTagName("documentation")[0].firstChild.nodeValue
            self.author = xml_content.getElementsByTagName("author")[0].firstChild.nodeValue
            self.email = xml_content.getElementsByTagName("author-email")[0].firstChild.nodeValue
            # list of files
            self.files = []
            xml_data = xml_content.getElementsByTagName("files")[0]
            for my_file in xml_data.getElementsByTagName("file"):
               data = {"path" :  my_file.attributes.get("path").value}
               self.files.append(data)
            # list of depandancies
            self.depandancies = []
            xml_data = xml_content.getElementsByTagName("depandancies")[0]
            for dep in xml_data.getElementsByTagName("dep"):
               data = {"name" :  dep.attributes.get("name").value}
               self.depandancies.append(data)

        except:
            raise PackageException("Error reading xml file : %s : %s" % (xml_file, str(traceback.format_exc())))








PM = PackageManager()
