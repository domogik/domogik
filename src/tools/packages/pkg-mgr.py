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
import shutil


PACKAGE_TYPES = ['plugin']
SRC_PATH = "../../../"
PLG_XML_PATH = "src/share/domogik/plugins/"
SETUP_PLUGIN_TPL = "./templates/setup-plugin.tpl"
TMP_EXTRACT_DIR = "domogik-pkg-mgr" # used with /tmp (or assimilated) before
REPO_SRC_FILE = "/etc/domogik/sources.list"
REPO_LST_FILE = "packages.lst"
REPO_LST_FILE_HEADER = "Domogik repository"
REPO_CACHE_DIR = "/var/cache/domogik"

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
        parser.add_option("-l", "--list",
                          action = "store_true", 
                          dest = "action_list",
                          default = False,
                          help = "Display cache's package list")
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
        if (self.options.action_update == False \
                and self.options.action_list == False )\
                and len(self.args) != 1:
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
                print("Error : --type should not be used with update option")
                return
            if self.options.output_dir != None:
                print("Error : --output-dir should not be used with update option")
                return

            # update list
            self._update_list()

        # list packages in cache
        if self.options.action_list == True:
            # check package type and -o
            if self.options.package_type != None:
                print("Error : --type should not be used with list option")
                return
            if self.options.output_dir != None:
                print("Error : --output-dir should not be used with list option")
                return

            # update list
            self._list_packages()
        

    def _create_package_for_plugin(self, name, output_dir):
        """ Create package for a plugin
            1. read xml file to get informations and list of files
            2. generate package
            @param name : name of plugin
        """
        print("Plugin nam : %s" % name)

        try:
            plg_xml = PackageXml(name)
        except:
            print(str(traceback.format_exc()))
            return
        print("Xml file OK")

        # TODO : add a check on type = "plugin"

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
        # Get repositories list
        try:
            # Read repository source file and generate repositories list
            repo_list = self._get_repositories_list(REPO_SRC_FILE)
        except:
            print(str(traceback.format_exc()))
            return
             
        # Clean cache folder
        try:
            self._clean_cache(REPO_CACHE_DIR)
        except:
            print(str(traceback.format_exc()))
            return
             
        # for each list, get files and associated xml
        try:
            self._parse_repository(repo_list, REPO_CACHE_DIR)
        except:
            print(str(traceback.format_exc()))
            return


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
        # return sorted list
        return sorted(repo_list, key = lambda k: k['priority'], reverse = True)


    def _clean_cache(self, folder):
        """ If not exists, create <folfer>
            Then, clean this folder
            @param folder : cache folder to empty
        """
        # Create folder
        try:
            if os.path.isdir(folder) == False:
                os.makedirs(folder)
        except:
            raise PackageException("Error while creating cache folder '%s' : %s" % (folder, traceback.format_exc()))

        # Clean folder
        try:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
        except:
            raise PackageException("Error while cleaning cache folder '%s' : %s" % (folder, traceback.format_exc()))


    def _parse_repository(self, repo_list, cache_folder):
        """ For each repo, get file list, check if it is higher version and
            get package's xml
            @param repo_list : repositories list
            @param cache_folder : package cache folder
        """
        package_list = []

        # get all packages url
        file_list = []
        for repo in repo_list:
            file_list.extend(self._get_files_list_from_repository(repo["url"]))

        # for each package, put it in cache if higher version
        for url_prefix in file_list:
            pkg_xml = PackageXml(url = "%s.xml" % url_prefix)
            print("Add '%s (%s)' in cache" % (pkg_xml.name, pkg_xml.version))
            pkg_xml.cache_package(cache_folder, url_prefix)


    def _get_files_list_from_repository(self, url):
        """ Read packages.xml on repository
            @param url : repo url
        """
        try:
            resp = urllib.urlopen("%s/%s" % (url, REPO_LST_FILE))
            my_list = []
            first_line = True
            for data in resp.readlines():
                if first_line == True:
                    first_line = False
                    if data.strip() != REPO_LST_FILE_HEADER:
                        print("This is not a Domogik repository : '%s/%s'" %
                                   (url, REPO_LST_FILE))
                        break
                else:
                    my_list.append("%s/%s" % (url, data.strip()))
            return my_list
        except IOError:
            print("Bad url :'%s/%s'" % (url, REPO_LST_FILE))
            return []


    def _list_packages(self):
        """ List all packages in cache folder 
        """
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for f in files:
                pkg_xml = PackageXml(path = "%s/%s" % (root, f))
                pkg_list.append({"fullname" : pkg_xml.fullname,
                                 "version" : pkg_xml.version,
                                 "desc" : pkg_xml.desc})
        pkg_list =  sorted(pkg_list, key = lambda k: (k['fullname'], 
                                                      k['version']))
        for pkg in pkg_list:
             print("%s (%s) : %s" % (pkg["fullname"], 
                                     pkg["version"], 
                                     pkg["desc"]))

    def _show_packages(self, name, version = None):
        """ Show a package description
        """
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for f in files:
                pkg_xml = PackageXml(path = "%s/%s" % (root, f))
              


class PackageXml():
    def __init__(self, name = None, url = None, path = None):
        """ Read xml file of a plugin and make an object from it
            @param name : name of plugin
            @param url : url of xml file
            @param path : path of xml file
        """
        try:
            if name != None:
                # get config
                cfg = Loader('domogik')
                config = cfg.load()
                conf = dict(config[1])
                xml_plugin_directory = "%s/%s" % (SRC_PATH, PLG_XML_PATH)
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
        except:
            raise PackageException("Error reading xml file : %s : %s" % (xml_file, str(traceback.format_exc())))


    def cache_package(self, cache_folder, url_prefix):
        """ Add url_prefix info in xml data
            Store xml in a file in cache_folder
            @param cache_folder : folder to put xml file
            @param url_prefix : http://.../pluginname-version
        """
        top_elt = self.xml_content.documentElement
        new_elt = self.xml_content.createElementNS(None, 'repository')
        new_elt.setAttribute("url_prefix", url_prefix)
        top_elt.appendChild(new_elt)
        cache_file = open("%s/%s" % (cache_folder, self.xml_filename), "w") 
        cache_file.write(self.xml_content.toxml().encode("utf-8"))
        cache_file.close()




PM = PackageManager()
