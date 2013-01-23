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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.packagejson import PackageJson, PackageException
from domogik.common.packagedata import PackageData
from domogik.common.configloader import Loader
import traceback
import tarfile
import tempfile
import os
import pwd
import urllib
import shutil
import sys
from domogik.common import logger
from distutils2.version import NormalizedVersion 
import json
import re
import zipfile

from domogik import __path__ as domopath
SRC_PATH = "%s/" % os.path.dirname(os.path.dirname(domopath[0]))
DOC_PATH = "src/domogik_packages/docs/" 

CONFIG_FOLDER = "/etc/domogik/"
CACHE_FOLDER = "/var/cache/domogik/"
LIB_FOLDER = "/var/lib/domogik/"

TMP_EXTRACT_DIR = "%s/tmp/" % CACHE_FOLDER
CONFIG_FILE = "%s/domogik.cfg" % CONFIG_FOLDER
REPO_SRC_FILE = "%s/sources.list" % CONFIG_FOLDER
REPO_CACHE_DIR = "%s/cache" % CACHE_FOLDER
ICON_CACHE_DIR = "%s/images" % REPO_CACHE_DIR
PKG_CACHE_DIR = "%s/pkg-cache" % CACHE_FOLDER
REPO_LST_FILE_HEADER = "Domogik Repository"

cfg = Loader('domogik')
config = cfg.load()
conf = dict(config[1])
if conf.has_key('package_path'):
    INSTALL_PATH = conf['package_path']
    PACKAGE_MODE = True
else:
    INSTALL_PATH = "/tmp/"
    PACKAGE_MODE = False

cfg = Loader('rest')
config = cfg.load()
conf = dict(config[1])
REST_URL = "http://%s:%s" % (conf["rest_server_ip"], conf ["rest_server_port"])

PLUGIN_JSON_PATH = "%s/domogik_packages/plugins" % INSTALL_PATH
EXTERNAL_JSON_PATH = "%s/domogik_packages/externals" % INSTALL_PATH

# type of part for a plugin
PKG_PART_XPL = "xpl"
PKG_PART_RINOR = "rinor"

class PackageManager():
    """ Tool to create packages
    """

    def __init__(self):
        """ Init tool
        """
        log = logger.Logger("package-manager")
        self._log = log.get_logger("package-manager")

    def log(self, message):
        """ Log and print message
            @param message : data to log
        """
        self._log.info(message)
        print(message)


    def _create_package_for_plugin(self, id, output_dir, force):
        """ Create package for a plugin
            1. read json file to get informations and list of files
            2. generate package
            @param id : name of plugin
            @param output_dir : target directory for package
            @param force : False : ask for confirmation
        """
        self.log("Plugin id : %s" % id)
        if PACKAGE_MODE == True:
            msg = "Domogik in 'production' mode (packages management activated) : creating a package is not possible"
            self.log(msg)
            return

        try:
            pkg_obj = PackageJson(id)
            pkg_json = pkg_obj.json
        except:
            self.log(str(traceback.format_exc()))
            return

        # check version format
        try:
            NormalizedVersion(pkg_json["identity"]["version"])
        except:
            self.log("Plugin version '%s' is not valid. Exiting." % pkg_json["identity"]["version"])
            return
        try:
            NormalizedVersion(pkg_json["identity"]["domogik_min_version"])
        except:
            self.log("Domogik min version '%s' is not valid. Exiting." % pkg_json["identity"]["domogik_min_version"])
            return

        self.log("Json file OK")

        # check type == plugin
        if pkg_json["identity"]["type"] != "plugin":
            self.log("Error : this package is not a plugin")
            return

        # display plugin informations
        pkg_obj.display()

        # check files exist
        if pkg_json["files"] == []:
            self.log("There is no file defined : the package won't be created")
            return

        # check doc files exist
        doc_path = DOC_PATH + "/plugin/%s/" % id
        doc_fullpath = SRC_PATH + doc_path
        if not os.path.isdir(doc_fullpath):
            self.log("There is no documentation files in '%s' : the package won't be created" % doc_fullpath)
            return

        if force == False:
            self.log("\nAre these informations OK ?")
            resp = raw_input("[o/N]")
            if resp.lower() != "o":
                self.log("Exiting...")
                return

        # Copy Json file in a temporary location in order to complete it
        json_tmp_file = "%s/plugin-%s-%s.json" % (tempfile.gettempdir(),
                                                pkg_json["identity"]["id"],
                                                pkg_json["identity"]["version"])
        shutil.copyfile(pkg_json["identity"]["info_file"], json_tmp_file)
        
        # Update info.json with generation date
        pkg_obj.set_generated(json_tmp_file)

        # Create .tgz
        self._create_tar_gz("plugin-%s-%s" % (pkg_json["identity"]["id"], pkg_json["identity"]["version"]), 
                            output_dir,
                            pkg_json["all_files"],
                            json_tmp_file,
                            pkg_json["identity"]["icon_file"],
                            doc_fullpath)

    def _create_package_for_external(self, id, output_dir, force):
        """ Create package for a external
            1. read json file to get informations and list of files
            2. generate package
            @param id : name of external
            @param output_dir : target directory for package
            @param force : False : ask for confirmation
        """
        self.log("Hardware id : %s" % id)
        if PACKAGE_MODE == True:
            msg = "Domogik in 'production' mode (packages management activated) : creating a package is not possible"
            self.log(msg)
            return

        try:
            pkg_obj = PackageJson(id, pkg_type = "external")
            pkg_json = pkg_obj.json
        except:
            self.log(str(traceback.format_exc()))
            return

        # check version format
        try:
            NormalizedVersion(pkg_json["identity"]["version"])
        except:
            self.log("Plugin version '%s' is not valid. Exiting." % pkg_json["identity"]["version"])
            return
        try:
            NormalizedVersion(pkg_json["identity"]["domogik_min_version"])
        except:
            self.log("Domogik min version '%s' is not valid. Exiting." % pkg_json["identity"]["domogik_min_version"])
            return

        self.log("Json file OK")

        if pkg_json["identity"]["type"] != "external":
            self.log("Error : this package is not an external member")
            return

        # display external informations
        pkg_obj.display()

        # check file existence
        if pkg_json["files"] == []:
            self.log("There is no file defined : the package won't be created")
            return

        # check doc files exist
        doc_path = DOC_PATH + "/external/%s/" % id
        doc_fullpath = SRC_PATH + doc_path
        if not os.path.isdir(doc_fullpath):
            self.log("There is no documentation files in '%s' : the package won't be created" % doc_fullpath)
            return

        if force == False:
            self.log("\nAre these informations OK ?")
            resp = raw_input("[o/N]")
            if resp.lower() != "o":
                self.log("Exiting...")
                return

        # Copy Json file in a temporary location in order to complete it
        json_tmp_file = "%s/external-%s-%s.json" % (tempfile.gettempdir(),
                                                pkg_json["identity"]["id"],
                                                pkg_json["identity"]["version"])
        shutil.copyfile(pkg_json["identity"]["info_file"], json_tmp_file)
        
        # Update info.json with generation date
        pkg_obj.set_generated(json_tmp_file)

        # Create .tgz
        self._create_tar_gz("external-%s-%s" % (pkg_json["identity"]["id"], pkg_json["identity"]["version"]), 
                            output_dir,
                            pkg_json["all_files"], 
                            json_tmp_file,
                            pkg_json["identity"]["icon_file"],
                            doc_fullpath)


    def _create_tar_gz(self, name, output_dir, files, info_file = None, icon_file = None, doc_path = None):
        """ Create a .tar.gz file anmmed <name.tgz> which contains <files>
            @param name : file name
            @param output_dir : if != None, the path to put .tar.gz
            @param files : table of file names to add in tar.gz
            @param info_file : path for info.json file
            @param icon_file : path for icon.png file
            @param doc_path : path for doc
        """
        if output_dir == None:
            my_tar = "%s/%s.tgz" % (tempfile.gettempdir(), name)
        else:
            my_tar = "%s/%s.tgz" % (output_dir, name)
        self.log("Generating package : '%s'" % my_tar)
        try:
            tar = tarfile.open(my_tar, "w:gz")
            for my_file in files:
                path =  str(my_file)
                self.log("- %s" % path)
                if os.path.isfile(SRC_PATH + path):
                    tar.add(SRC_PATH + path, arcname = path)
                elif os.path.isdir(SRC_PATH + path):
                    self.log("  (directory)")
                    tar.add(SRC_PATH + path, arcname = path)
                else:
                    self.log("  WARNING : file doesn't exists : %s" % SRC_PATH + path)
            if info_file != None:
                self.log("- info.json")
                tar.add(info_file, arcname="info.json")
            if icon_file != None:
                if os.path.isfile(icon_file):
                    self.log("- icon.png")
                    tar.add(icon_file, arcname="icon.png")
            if doc_path != None:
                self.log("- package documentation")
                tar.add(doc_path, arcname="docs")
            tar.close()

            # delete temporary Json file
            if info_file != None:
                os.unlink(info_file) 
        except: 
            msg = "Error generating package : %s : %s" % (my_tar, traceback.format_exc())
            self.log(msg)
            # delete temporary Json file
            if info_file != None:
                os.unlink(info_file) 
            raise PackageException(msg)
        self.log("OK")
    

    def cache_package(self, cache_dir, pkg_type, id, version, pkg_path = None):
        """ Download package to put it in cache
            @param cache_dir : folder in which we want to cache the file
            @param pkg_type : package type
            @param id : package id
            @param version : package version
            @param pkg_path : path of the package to cache on local host
        """
        if PACKAGE_MODE != True:
            raise PackageException("Package mode not activated")
        dl_path = "%s/%s-%s-%s.tgz" % (cache_dir, pkg_type, id, version)

        ### cache from the web
        if pkg_path == None:
            package = "%s-%s" % (pkg_type, id)
            pkg, status = self._find_package(package, version)
            if status != True:
                return False
            # download package
            path = pkg["archive_url"]
            self.log("Caching package : '%s' to '%s'" % (path, dl_path))
            urllib.urlretrieve(path, dl_path)
        ### cache from a local file
        else:
            self.log("Caching package : '%s' to '%s'" % (pkg_path, dl_path))
            shutil.copyfile(pkg_path, dl_path)
        self.log("OK")
        return True

    def _create_folder(self, folder):
        """ Try to create a folder (does nothing if it already exists)
            @param folder : folder path
        """
        try:
            if os.path.isdir(folder) == False:
                self.log("Creating directory : %s" % folder)
                os.makedirs(folder)
        except:
            msg = "Error while creating temporary folder '%s' : %s" % (folder, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)

    def install_package(self, path, version = None, package_part = PKG_PART_XPL):
        """ Install a package
            0. Eventually download package
            1. Extract tar.gz
            2. Install package
            3. Insert data in database
            @param path : path for tar.gz
            @param version : version to install (default : highest)
            @param package_part : PKG_PART_XPL (for manager), PKG_PART_RINOR (for RINOR)
        """
        if PACKAGE_MODE != True:
            raise PackageException("Package mode not activated")
        self.log("Start install for part '%s' of '%s'" % (package_part, path))
        if path[0:6] == "cache:":
            path = "%s/package/download/%s" % (REST_URL, path[6:])

        if path[0:5] == "repo:":
            pkg, status = self._find_package(path[5:], version)
            if status != True:
                return status
            path = pkg.archive_url

        # get package name
        if path[0:4] == "http": # special process for a http path
            id = full_name = '-'.join(path.split("/")[-3:])
            print("id=%s" % full_name)
        else:
            full_name = os.path.basename(path)
            # twice to remove first .gz and then .tar
            id =  os.path.splitext(full_name)[0]
            id =  os.path.splitext(id)[0] 

        self.log("Ask for installing package id : %s" % id)

        # get temp dir to extract data
        my_tmp_dir_dl = TMP_EXTRACT_DIR
        my_tmp_dir = "%s/%s" % (my_tmp_dir_dl, id)
        self._create_folder(my_tmp_dir)

        # Check if we need to download package
        if path[0:4] == "http":
            dl_path = "%s/%s.tgz" % (my_tmp_dir_dl, full_name)
            self.log("Downloading package : '%s' to '%s'" % (path, dl_path))
            urllib.urlretrieve(path, dl_path)
            path = dl_path
            self.log("Package downloaded : %s" % path)

        # extract in tmp directory
        self.log("Extracting package...")
        try:
            self._extract_package(path, my_tmp_dir)
        except:
            msg = "Error while extracting package '%s' : %s" % (path, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)
        self.log("Package successfully extracted.")

        # get Json informations
        pkg_json = PackageJson(path = "%s/info.json" % my_tmp_dir).json

        # check compatibility with domogik installed version
        __import__("domogik")
        dmg = sys.modules["domogik"]
        self.log("Domogik version = %s" % dmg.__version__)
        self.log("Minimum Domogik version required for package = %s" % pkg_json["identity"]["domogik_min_version"])
        print("%s < %s" % ( pkg_json["identity"]["domogik_min_version"] , dmg.__version__))
        if pkg_json["identity"]["domogik_min_version"] > dmg.__version__:
            msg = "This package needs a Domogik version >= %s. Actual is %s. Installation ABORTED!" % (pkg_json["identity"]["domogik_min_version"], dmg.__version__)
            self.log(msg)
            raise PackageException(msg)

        # create install directory
        self._create_folder(INSTALL_PATH)

        # install plugin in $HOME
        self.log("Installing package (%s)..." % pkg_json["identity"]["type"])
        try:
            if pkg_json["identity"]["type"] in ('plugin', 'external'):
                self._install_plugin_or_external(my_tmp_dir, INSTALL_PATH, pkg_json["identity"]["type"], package_part)
            else:
                raise "Package type '%s' not installable" % pkg_json["identity"]["type"]
        except:
            msg = "Error while installing package : %s" % (traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)
        self.log("Package successfully extracted.")

        # insert data in database
        if pkg_json["identity"]["type"] in ('plugin', 'external'):
            if package_part == PKG_PART_RINOR:
                self.log("Insert data in database...")
                pkg_data = PackageData("%s/info.json" % my_tmp_dir)
                pkg_data.insert()

        self.log("Package installation finished")
        return True


    def uninstall_package(self, pkg_type, id):
        """ Uninstall a package
            For the moment, we will only delete the package Json file for 
            plugins and external
            @param pkg_type : package type
            @param id : package id
        """
        if PACKAGE_MODE != True:
            raise PackageException("Package mode not activated")
        self.log("Start uninstall for package '%s-%s'" % (pkg_type, id))
        self.log("Only Json description file will be deleted in this Domogik version")

        try:
            if pkg_type in ('plugin'):
                os.unlink("%s/domogik_packages/plugins/%s.json" %(INSTALL_PATH, id))
            elif pkg_type in ('external'):
                os.unlink("%s/domogik_packages/externals/%s.json" %(INSTALL_PATH, id))
            else:
                raise PackageException("Package type '%s' not uninstallable" % pkg_type)
        except:
            msg = "Error while unstalling package : %s" % (traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)
        self.log("Package successfully uninstalled.")

        return True


    def _extract_package(self, pkg_path, extract_path):
        """ Extract package <pkg_path> in <extract_path>
            @param pkg_path : path to package
            @param extract_path : path for extraction
        """
        tar = tarfile.open(pkg_path)
        # check if there is no .. or / in files path
        for fic in tar.getnames():
            if fic[0:1] == "/" or fic[0:2] == "..":
                msg = "Error while extracting package '%s' : filename '%s' in tgz not allowed" % (pkg_path, fic)
                self.log(msg)
                raise PackageException(msg)
        tar.extractall(path = extract_path)
        tar.close()


    def _install_plugin_or_external(self, pkg_dir, install_path, pkg_type, package_part):
        """ Install plugin
            @param pkg_dir : directory where package is extracted
            @param install_path : path where we install packages
            @param pkg_type : plugin, external
            @param pkg_id : package id
            @param package_part : PKG_PART_XPL (for manager), PKG_PART_RINOR (for RINOR)
            @param repo_source : path from which the package comes
        """

        ### create needed directories
        # create install directory
        self.log("Creating directories for %s..." % pkg_type)
        plg_path = "%s/domogik_packages/" % (install_path)
        self._create_folder(plg_path)

        ### copy files
        self.log("Copying files for %s..." % pkg_type)
        try:
            # xpl/* and plugins/*.json are installed on target host 
            if package_part == PKG_PART_XPL:
                if pkg_type == "plugin":
                    copytree("%s/src/domogik_packages/xpl" % pkg_dir, "%s/xpl" % plg_path, self.log)
                    copytree("%s/src/domogik_packages/tests" % pkg_dir, "%s/tests" % plg_path, self.log)
                    self._create_init_py("%s/" % plg_path)
                    self._create_init_py("%s/xpl/" % plg_path)
                    self._create_init_py("%s/xpl/bin/" % plg_path)
                    self._create_init_py("%s/xpl/lib/" % plg_path)
                    self._create_init_py("%s/xpl/helpers/" % plg_path)
                    self._create_init_py("%s/tests/" % plg_path)
                    self._create_init_py("%s/tests/plugin/" % plg_path)
                    type_path = "plugins"
                if pkg_type == "external":
                    type_path = "externals"
                print("%s => %s" % ("%s/src/share/domogik/%ss" % (pkg_dir, pkg_type), "%s/%s" % (plg_path, type_path)))
                copytree("%s/src/share/domogik/%ss" % (pkg_dir, pkg_type), "%s/%s" % (plg_path, type_path), self.log)
                copytree("%s/src/share/domogik/data/" % pkg_dir, "%s/data/" % plg_path, self.log)

            # design/*
            # stats/* 
            # url2xpl/* 
            # exernal/* are installed on rinor host
            if package_part == PKG_PART_RINOR:
                copytree("%s/src/share/domogik/design/" % pkg_dir, "%s/design/" % plg_path, self.log)
                copytree("%s/src/share/domogik/url2xpl/" % pkg_dir, "%s/url2xpl/" % plg_path, self.log)
                copytree("%s/src/share/domogik/stats/" % pkg_dir, "%s/stats/" % plg_path, self.log)
                copytree("%s/src/external/" % pkg_dir, "%s/external" % plg_path, self.log)
        except:
            msg = "Error while copying %s files : %s" % (pkg_type, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)


    def _create_init_py(self, path):
        """ Create __init__.py file in path
            param path : path where we wan to create the file
        """
        try:
            self.log("Create __init__.py file in %s" % path)
            open("%s/__init__.py" % path, "a").close()
        except IOError as (errno, strerror):
            if errno == 2:
                self.log("No directory '%s'" % path)
                return
            raise
        except:
            msg = "Error while creating __init__.py file in %s : %s" % (path, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)



    def update_cache(self):
        """ update local package cache
        """
        if PACKAGE_MODE != True:
            self.log("Update cache not possible : Package mode not activated")
            return
        # Get repositories list
        try:
            # Read repository source file and generate repositories list
            repo_list = self.get_repositories_list()
        except:
            self.log(str(traceback.format_exc()))
            return False
             
        # Clean cache folder
        try:
            self._clean_cache(REPO_CACHE_DIR)
        except:
            self.log(str(traceback.format_exc()))
            return False
             
        # for each repository, get files and associated Json
        # the higher priority is processed first. If a package is duplicate, for
        # the lower priorities, it will be skipped
        try:
            for my_repo in repo_list:
                self._cache_repository(my_repo["url"], my_repo["priority"], REPO_CACHE_DIR)
        except:
            self.log(str(traceback.format_exc()))
            return False

        return True

    def get_repositories_list(self):
        """ Read repository source file and return list
        """
        try:
            repo_list = []
            src_file = open(REPO_SRC_FILE, "r")
            for line in src_file.readlines():
                # if the line is not a comment
                if line.strip()[0] != "#": 
                    url = line.split()[1]
                    # remove all useless final "/"
                    while url[-1] == "/":
                        url = url[0:-1]
                    repo_list.append({"priority" : line.split()[0],
                                      "url" : url})
            src_file.close()
        except:
            msg = "Error reading source file : %s : %s" % (REPO_SRC_FILE, str(traceback.format_exc()))
            self.log(msg)
            raise PackageException(msg)
        # return sorted list
        return sorted(repo_list, key = lambda k: k['priority'], reverse = True)

    def _cache_repository(self, base_url, priority, cache_dir):
        """ Download the json describing the repository
            @param base_url : repo url in sources.list
            @param priority : repo priority
            @param cache_dir : dir for the cache
        """
        ### read status json
        repo_status_url = "%s" % base_url
        self.log("Processing '%s'..." % repo_status_url)
        resp = urllib.urlopen(repo_status_url)
        repo_json = json.load(resp)
        self.log("Counter = %s" % repo_json["count"])

        ### download tgz data
        repo_data_url = "%s/data" % base_url
        tmp_repo_dir = "%s/%s" % (cache_dir, \
                                   re.sub('\W+', '_', repo_data_url))
        tmp_repo_file = "%s.tgz" % tmp_repo_dir
        repo_json = "%s.json" % tmp_repo_dir
        urllib.urlretrieve(repo_data_url, \
                           tmp_repo_file)

        ### extract tgz data
        self._create_folder(tmp_repo_dir)

        # dirty trick for ferllings bug
        #my_zip = zipfile.ZipFile(tmp_repo_file) 
        #my_zip.extractall(path = tmp_repo_dir)

        my_tar = tarfile.open(tmp_repo_file)
        my_tar.extractall(path = tmp_repo_dir)
        my_tar.close()

        ### Remove tgz file
        os.unlink(tmp_repo_file)

        ### Move json from tgz extracted and complete it
        my_json = json.load(open("%s/repo.info" % tmp_repo_dir))
        for my_pkg in my_json["packages"]:
            my_pkg["priority"] = priority
        my_file = open(repo_json, "w")
        my_file.write(json.dumps(my_json, sort_keys=True, indent=4))
        my_file.close()

        ### Move icons from tgz extracted
        icon_dir = "%s/images/" % cache_dir
        self._create_folder(icon_dir)
        for root, dirs, files in os.walk("%s/images/" % tmp_repo_dir):
            for fic in files:
                if fic[-4:] == ".png":
                    shutil.move("%s/%s" % (root, fic), \
                                icon_dir)

        ### Delete the directory
        self._clean_folder(tmp_repo_dir) 
        os.rmdir(tmp_repo_dir)

    def _clean_cache(self, folder):
        """ If not exists, create <folder>
            Then, clean this folder
            @param folder : cache folder to empty
        """
        # Create folder
        self._create_folder(folder)

        # clean folder
        self._clean_folder(folder)


    def _clean_folder(self, folder):
        """ Delete the content of a folder
            @param folder: folder to clean
        """
        # Clean folder
        try:
            for root, dirs, files in os.walk(folder):
                for fic in files:
                    os.unlink(os.path.join(root, fic))
                for dir in dirs:
                    shutil.rmtree(os.path.join(root, dir))
        except:
            msg = "Error while cleaning cache folder '%s' : %s" % (folder, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)

    def get_available_updates(self, pkg_type, pkg_id, version):
        """ List all available updates for a package
            @param pkg_type : package type
            @param id : package id
            @param version : package version
        """
        if PACKAGE_MODE != True:
            raise PackageException("Package mode not activated")
        
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for fic in files:
                if fic[-5:] != ".json":
                    continue
                my_json = json.load(open("%s/%s" % (root, fic)))
                for my_pkg in my_json["packages"]:
                    if pkg_type == my_pkg["type"] and \
                       pkg_id == my_pkg["id"] and \
                       version < my_pkg["version"]:
                        pkg_list.append({"type" : pkg_type,
                                         "id" : pkg_id,
                                         "version" : my_pkg["version"],
                                         "priority" : my_pkg["priority"], 
                                         "changelog" : my_pkg["changelog"]})
        return pkg_list
                       
    def list_packages(self):
        """ List all packages in cache folder 
            Used for printing on command line
        """
        pkg_list = []
        
        print self.get_packages_list()
        #TODO  :review output format


    def _get_package_priority_in_cache(self, fullname, version):
        """ Get priority of a cache package/version
            @param fullname : fullname of package
            @param version : package's version
        """

        # TODO : to review

        #for root, dirs, files in os.walk(REPO_CACHE_DIR):
        #    for fic in files:
        #        if fic[-5:] == ".json":
        #            pkg_json = PackageJson(path = "%s/%s" % (root, fic)).json
        #            if fullname == pkg_json["identity"]["fullname"] and version == pkg_json["identity"]["version"]:
        #                return pkg_json["identity"]["priority"]
        #return None

    def get_packages_list(self, fullname = None, version = None, pkg_type = None):
        """ List all packages in cache folder 
            and return a detailed list
            @param fullname (optionnal) : fullname of a package
            @param version (optionnal) : version of a package (to use with name)
            @param pkg_type (optionnal) : package type
            Used by Rest
        """
        if PACKAGE_MODE != True:
            raise PackageException("Package mode not activated")

        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for fic in files:
                if fic[-5:] != ".json":
                    continue
                my_json = json.load(open("%s/%s" % (root, fic)))
                for my_pkg in my_json["packages"]:
                    if fullname == None or (fullname == my_pkg["fullname"] and version == my_pkg["version"]):
                        if pkg_type == None or pkg_type == my_pkg["type"]:
                            pkg_list.append(my_pkg)
        return sorted(pkg_list, key = lambda k: (k['id']))

        # FOR HISTORY (temp) : 
        #                    pkg_list.append({"id" : pkg_json["identity"]["id"],
        #                                 "type" : pkg_json["identity"]["type"],
        #                                 "fullname" : pkg_json["identity"]["fullname"],
        #                                 "version" : pkg_json["identity"]["version"],
        #                                 "source" : pkg_json["identity"]["source"],
        #                                 "generated" : pkg_json["identity"]["generated"],
        #                                 "techno" : pkg_json["identity"]["category"],
        #                                 "doc" : pkg_json["identity"]["documentation"],
        #                                 "desc" : pkg_json["identity"]["description"],
        #                                 "changelog" : pkg_json["identity"]["changelog"],
        #                                 "author" : pkg_json["identity"]["author"],
        #                                 "email" : pkg_json["identity"]["author_email"],
        #                                 "domogik_min_version" : pkg_json["identity"]["domogik_min_version"],
        #                                 "priority" : pkg_json["identity"]["priority"],
        #                                 "dependencies" : pkg_json["dependencies"],
        #                                 "archive_url" : pkg_json["identity"]["archive_url"]})

    def get_installed_packages_list(self):
        """ List all packages in install folder 
            and return a detailed list
        """
        if PACKAGE_MODE != True:
            raise PackageException("Package mode not activated")
        pkg_list = []
        for rep in [PLUGIN_JSON_PATH, EXTERNAL_JSON_PATH]:
            for root, dirs, files in os.walk(rep):
                for fic in files:
                    if fic[-5:] == ".json":
                        pkg_json = PackageJson(path = "%s/%s" % (root, fic)).json
                        # TODO : replace by identity and repo informations
                        #   from the json ???
                        pkg_list.append(pkg_json["identity"])
        return sorted(pkg_list, key = lambda k: (k['fullname'], 
                                                 k['version']))

    def show_packages(self, fullname, version = None):
        """ Show a package description
            @param fullname : fullname of package (type-name)
            @param version : optionnal : version to display (if several)
        """
        pkg_obj, status = self._find_package(fullname, version)
        if status == True:
            pkg_obj.display()


    def _find_package(self, fullname, version = None):
        """ Find a package and return 
                               - json data or None if not found
                               - a status : True if ok, a message elsewhere
            @param fullname : fullname of package (type-name)
            @param version : optionnal : version to display (if several)
        """
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for fic in files:
                if fic[-5:] != ".json":
                    continue
                print fic
                my_json = json.load(open("%s/%s" % (root, fic)))
                for my_pkg in my_json["packages"]:
                    if (version == None and \
                        fullname == my_pkg["fullname"]) or \
                       (version == my_pkg["version"] and \
                        fullname == my_pkg["fullname"]):
                        pkg_list.append(my_pkg)
                       
        if len(pkg_list) == 0:
            if version == None:
                version = "*"
            msg = "No package corresponding to '%s' in version '%s'" % (fullname, version)
            self.log(msg)
            return [], msg
        if len(pkg_list) > 1:
            msg = "Several packages are available for '%s'. Please specify which version you choose" % fullname
            self.log(msg)
            for pkg in pkg_list:
                self.log("%s (%s, prio: %s)" % (pkg["fullname"], 
                                              pkg["version"],
                                              pkg["priority"]))
            return [], msg

        return pkg_list[0], True

##### shutil.copytree fork #####
# the fork is necessary because original function raise an error if a directory
# already exists. In our case, some directories will exists!

class Error(EnvironmentError):
    """ Error
    """
    pass

try:
    WindowsError
except NameError:
    WindowsError = None


def copytree(src, dst, cb_log):
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

    """
    try:
        names = os.listdir(src)
    except OSError as (errno, strerror):
        if errno == 2:
            cb_log("No data for '%s'" % src)
            return
        raise

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
        cb_log("%s => %s" % (srcname, dstname))
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dstname, cb_log)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error, errors
    



