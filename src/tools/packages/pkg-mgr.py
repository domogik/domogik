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

from domogik.common.packagexml import PackageXml, PackageException
from insert_data import PackageData
from domogik.common.configloader import Loader
from optparse import OptionParser
from xml.dom import minidom
import traceback
import tarfile
import tempfile
import os
import pwd
from subprocess import Popen
import urllib
from operator import attrgetter
import shutil


PACKAGE_TYPES = ['plugin']
SRC_PATH = "../../../"
PLG_XML_PATH = "src/share/domogik/plugins/"
TMP_EXTRACT_DIR = "domogik-pkg-mgr" # used with /tmp (or assimilated) before
REPO_SRC_FILE = "/etc/domogik/sources.list"
REPO_LST_FILE = "packages.lst"
REPO_LST_FILE_HEADER = "Domogik repository"
REPO_CACHE_DIR = "/var/cache/domogik"
DOMOGIK_DEFAULT = "/etc/default/domogik"
INSTALL_PATH = "%s/.domogik/" % os.getenv("HOME")


class PackageManager():
    """ Tool to create packages
    """

    def __init__(self):
        """ Init tool
        """
        self.dmg_user = self.get_config_path()

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
        parser.add_option("-s", "--show",
                          action = "store_true", 
                          dest = "action_show",
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
                and len(self.args) < 1:
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
            if len(self.args) == 1:
                self._install_package(self.args[0])
            if len(self.args) == 2:
                self._install_package(self.args[0], self.args[1])

        # packages list update
        if self.options.action_update == True:
            self._update_list()

        # list packages in cache
        if self.options.action_list == True:
            self._list_packages()
        
        # show packages in cache
        if self.options.action_show == True:
            if len(self.args) == 1:
                self._show_packages(self.args[0])
            if len(self.args) == 2:
                self._show_packages(self.args[0], self.args[1])
        

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

        # check type == plugin
        if plg_xml.type != "plugin":
            print("Error : this package is not a plugin")
            return

        # display plugin informations
        plg_xml.display()

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

        # Create .tgz
        self._create_tar_gz("plugin-%s-%s" % (plg_xml.name, plg_xml.version), 
                            output_dir,
                            plg_xml.files, 
                            plg_xml.info_file)


    def _create_tar_gz(self, name, output_dir, files, info_file = None):
        """ Create a .tar.gz file anmmed <name.tgz> which contains <files>
            @param name : file name
            @param output_dir : if != None, the path to put .tar.gz
            @param files : table of file names to add in tar.gz
            @param info_file : path for info.xml file
        """
        if output_dir == None:
            my_tar = "%s/%s.tgz" % (tempfile.gettempdir(), name)
        else:
            my_tar = "%s/%s.tgz" % (output_dir, name)
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
            tar.close()
        except: 
            raise PackageException("Error generating package : %s : %s" % (my_tar, traceback.format_exc()))
        print("OK")
    

    def _install_package(self, path, version = None):
        """ Install a package
            0. Eventually download package
            1. Extract tar.gz
            2. Install package
            3. Insert data in database
            @param path : path for tar.gz
        """
        #if self.is_root() == False:
        #    print("-i option must be used as root")
        #    return
        # package from repository
        if path[0:5] == "repo:":
            pkg = self._find_package(path[5:], version)
            if pkg == None:
                return
            path = pkg.package_url

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
            raise PackageException("Error while creating temporary folder '%s' : %s" % (INSTALL_PATH, traceback.format_exc()))

        # Check if we need to download package
        if path[0:4] == "http":
            print("Downloading package : %s" % path)
            dl_path = "%s/%s" % (my_tmp_dir_dl, full_name)
            urllib.urlretrieve(path, dl_path)
            path = dl_path
            print("Package downloaded : %s" % path)

        # extract in tmp directory
        print("Extracting package...")
        try:
            self._extract_package(path, my_tmp_dir)
        except:
            raise PackageException("Error while extracting package '%s' : %s" % (path, traceback.format_exc()))
        print("Package successfully extracted.")

        # create install directory
        print("Creating install directory : %s" % INSTALL_PATH)
        try:
            if os.path.isdir(INSTALL_PATH) == False:
                os.makedirs(INSTALL_PATH)
        except:
            raise PackageException("Error while creating installation folder '%s' : %s" % (INSTALL_PATH, traceback.format_exc()))

        # install plugin in $HOME
        print("Installing package (plugin)...")
        try:
            self._install_plugin(my_tmp_dir, INSTALL_PATH)
        except:
            raise PackageException("Error while installing package : %s" % (traceback.format_exc()))
        print("Package successfully extracted.")

        # insert data in database
        pkg_data = PackageData("%s/info.xml" % my_tmp_dir, custom_path = "/home/%s/.domogik.cfg" % self.dmg_user)
        pkg_data.insert()

        print("Package installation finished")


    def _extract_package(self, pkg_path, extract_path):
        """ Extract package <pkg_path> in <extract_path>
            @param pkg_path : path to package
            @param extract_path : path for extraction
        """
        tar = tarfile.open(pkg_path)
        # check if there is no .. or / in files path
        for fic in tar.getnames():
            if fic[0:1] == "/" or fic[0:2] == "..":
                raise PackageException("Error while extracting package '%s' : filename '%s' not allowed" % (pkg_path, fic))
        tar.extractall(path = extract_path)
        tar.close()


    def _install_plugin(self, pkg_dir, install_path):
        """ Install plugin
            @param pkg_dir : directory where package is extracted
            @param install_path : path where we install packages
        """

        ### create needed directories
        # create install directory
        print("Creating directories for plugin...")
        plg_path = "%s/plugins/" % install_path
        try:
            if os.path.isdir(plg_path) == False:
                os.makedirs(plg_path)
        except:
            raise PackageException("Error while creating plugin folder '%s' : %s" % (plg_path, traceback.format_exc()))

        ### copy files
        print("Copying files for plugin...")
        try:
            copytree("%s/src/domogik" % pkg_dir, "%s/domogik" % plg_path)
            copytree("%s/src/share" % pkg_dir, "%s/share" % plg_path)
        except:
            raise PackageException("Error while copying plugin files : %s" % (traceback.format_exc()))




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
            file_list.extend(self._get_files_list_from_repository(repo["url"], repo["priority"]))

        # for each package, put it in cache if higher version
        for file_info in file_list:
            pkg_xml = PackageXml(url = "%s.xml" % file_info["file"])
            print("Add '%s (%s)' in cache" % (pkg_xml.name, pkg_xml.version))
            pkg_xml.cache_package(cache_folder, file_info["file"], file_info["priority"])


    def _get_files_list_from_repository(self, url, priority):
        """ Read packages.xml on repository
            @param url : repo url
            @param prioriry : repo priority
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
                    my_list.append({"file" : "%s/%s" % (url, data.strip()),
                                    "priority" : priority})
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
                                 "priority" : pkg_xml.priority,
                                 "desc" : pkg_xml.desc})
        pkg_list =  sorted(pkg_list, key = lambda k: (k['fullname'], 
                                                      k['version']))
        for pkg in pkg_list:
             print("%s (%s, prio: %s) : %s" % (pkg["fullname"], 
                                               pkg["version"], 
                                               pkg["priority"], 
                                               pkg["desc"]))

    def _show_packages(self, fullname, version = None):
        """ Show a package description
            @param fullname : fullname of package (type-name)
            @param version : optionnal : version to display (if several)
        """
        pkg = self._find_package(fullname, version)
        if pkg != None:
            pkg.display()


    def _find_package(self, fullname, version = None):
        """ Find a package and return xml data or None if not found
            @param fullname : fullname of package (type-name)
            @param version : optionnal : version to display (if several)
        """
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for f in files:
                pkg_xml = PackageXml(path = "%s/%s" % (root, f))
                if version == None:
                    if fullname == pkg_xml.fullname:
                        pkg_list.append({"fullname" : pkg_xml.fullname,
                                         "version" : pkg_xml.version,
                                         "priority" : pkg_xml.priority,
                                         "xml" : pkg_xml})
                else:
                    if fullname == pkg_xml.fullname and version == pkg_xml.version:
                        pkg_list.append({"fullname" : pkg_xml.fullname,
                                         "version" : pkg_xml.version,
                                         "priority" : pkg_xml.priority,
                                         "xml" : pkg_xml})
        if len(pkg_list) == 0:
            if version == None:
                version = "*"
            print("No package corresponding to '%s' in version '%s'" % (fullname, version))
            return None
        if len(pkg_list) > 1:
            print("Several packages are available for '%s'. Please specify which version you choose" % fullname)
            for pkg in pkg_list:
                 print("%s (%s, prio: %s)" % (pkg["fullname"], 
                                              pkg["version"],
                                              pkg["priority"]))
            return None

        return pkg_list[0]["xml"]

    def is_root(self):
        """ return True is current user is root
        """
        if pwd.getpwuid(os.getuid())[0] == "root":
            return True
        return False

    def get_config_path(self):
        """ get .domogik.cfg full path
        """
        try:
            file = open(DOMOGIK_DEFAULT, "r")
            for line in file.readlines():
                elt = line.split("=")
                if elt[0] == "DOMOGIK_USER":
                    dmg_user = elt[1].strip()
            file.close()
        except:
            raise PackageException("Error reading default file : %s : %s" % (DOMOGIK_DEFAULT, str(traceback.format_exc())))
        return dmg_user
              


class OLD_PackageXml():
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
            # list of dependencies
            self.dependencies = []
            xml_data = self.xml_content.getElementsByTagName("dependencies")[0]
            for dep in xml_data.getElementsByTagName("dep"):
               data = {"name" :  dep.attributes.get("name").value}
               self.dependencies.append(data)

            # construct filenames
            self.fullname = "%s-%s" % (self.type, self.name)
            self.xml_filename = "%s-%s-%s.xml" % (self.type, self.name, self.version)
            self.pkg_filename = "%s-%s-%s.tgz" % (self.type, self.name, self.version)

            # repository specifics
            rep = self.xml_content.getElementsByTagName("repository")
            if len(rep) == 0:
                self.package_url = None
                self.xml_url = None
                self.priority = None
            else:
                url_prefix = rep[0].attributes.get("url_prefix").value
                self.package_url = "%s.tgz" % url_prefix
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
        print("----- Plugin dependencies -------------------------------")
        for dep in self.dependencies:
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



##### shutil.copytree fork #####
# the fork is necessary because original function raise an error if a directory
# already exists. In our case, some directories will exists!

class Error(EnvironmentError):
    pass

try:
    WindowsError
except NameError:
    WindowsError = None


def copytree(src, dst):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)

    try:
        os.makedirs(dst)
    except OSError as (errno, strerror):
        if errno == 17:
            pass
        else:
            raise
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        print("%s => %s" % (srcname, dstname))
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dstname)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error, err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except OSError, why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error, errors

################################
if __name__ == "__main__":
    PM = PackageManager()
