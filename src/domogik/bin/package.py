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

Command line installer for packages

Implements
==========

- PackageInstaller

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik import __version__ as DMG_VERSION
from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.xpl.common.plugin import PACKAGES_DIR
from domogik.common.packagejson import PackageJson, PackageException
from argparse import ArgumentParser
import re
import os
import sys
import traceback
import zipfile
import json
import shutil
import requests
import magic
import tempfile
from distutils import version
import time


JSON_FILE = "info.json"

# allowed mime types for packages download
MIME_ZIP = 'application/zip'
ALLOWED_MIMES = [MIME_ZIP]

# download mode
STREAM = False
# True : will download the file part by part. Allow to display a progress bar or send progress over MQ
# False : just download

URL_REGEXP = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class PackageInstaller():
    """ Package installer class
    """
    def __init__(self):
        """ Init
        """
        l = logger.Logger("package")
        l.set_format_mode("messageOnly")
        self.log = l.get_logger()

        parser = ArgumentParser()
        parser.add_argument("-i", 
                          "--install", 
                          dest="install", 
                          help="Install a package from a path, a zip file or an url to a zip file or to a github repository and branch")
        parser.add_argument("-u", 
                          "--uninstall", 
                          dest="uninstall", 
                          help="Uninstall a package. Example : plugin_rfxcom")
        self.options = parser.parse_args()

        # get install path for packages
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        self.pkg_path = os.path.join(conf['libraries_path'], PACKAGES_DIR)

        # install a package
        if self.options.install:
            self.install(self.options.install)
 
        # uninstall a package
        elif self.options.uninstall:
            self.uninstall(self.options.uninstall)

        # no choice : display the list of installed packages
        else:
            self.list_packages()


    def install(self, package):
        """ Install a package
            Check what is the package
            if package is a folder : 
                check if it contains a info.json file and if it is ok/compliant. If so, create a symlink to it
            if package is a zip file :
                check if it contains a info.json file and if it is ok/compliant. If so, extract it
            if package is an url to a zip file :
                download the zip file, then process as a zip file
        """
        # check if the package is a folder
        if os.path.isdir(package):
            self.install_folder(package)

        # check if this is an url
        elif URL_REGEXP.search(package):
            downloaded_file, mime = self.download_from_url(package)
            if downloaded_file != None and mime == MIME_ZIP:
                self.install_zip_file(downloaded_file)

        # check if the package is a zip file
        elif zipfile.is_zipfile(package):
            self.install_zip_file(package)

        # the package format is not handled
        else:
            self.log.error("This tool doesn't handle this kind of package")
   

    def install_folder(self, path):
        """ Install the package from a folder
            If there is a correst json file, just create a symlink :)
        """
        path = os.path.realpath(path)
        self.log.info("Install a package from a folder : {0}".format(path))
        # check if there is the json file
        json_file = os.path.join(path, JSON_FILE)
        if not os.path.isfile(json_file):
            self.log.error("There is no json file in this folder : {0}".format(json_file))
            return

        # check if the json file is valid
        if not self.is_json_ok(json_file = json_file):
            return

        # if so, get the name of the package (symlink name)
        symlink_name = self.get_package_installation_name()

        # check it is not already installed
        # notice that this can't be done before as before we don't know the package name yet ;)
        if self.is_already_installed(symlink_name):
            return

        # and finally, create the symlink
        symlink_full = os.path.join(self.pkg_path, symlink_name)
        self.log.info("Create the symbolic link to {0} as {1}".format(path, symlink_full))
        try:
            os.symlink(path, symlink_full)
        except: 
            self.log.error("Error while creating the symbolic link to install the package : {0}".format(traceback.format_exc()))
            return
        self.log.info("Package installed!")
        

    def install_zip_file(self, path):
        """ Install the zip file
        """
        self.log.info("Install a package from a zip file : {0}".format(path))

        # check the zip file contains what we need
        with zipfile.ZipFile(path, 'r') as myzip:
            # test the zip file
            testzip = myzip.testzip()
            if testzip != None:
                self.log.error("The zip seems not to be good for the file : {0}".format(testzip))
                return

            # security!!!!! check if there is no .. or / in files path
            for fic in myzip.namelist():
                if fic[0:1] == "/" or fic[0:2] == "..":
                    self.log.error("Security issue ! The zip contains some files with a path starting by '/' or '..'")
                    return

            # we assume that the first item of the list is the master directory in the zip and so the info.json file is under it
            try:
                root_dir = myzip.namelist()[0]
            except:
                self.log.error("Error while looking in the zip file : {0}".format(traceback.format_exc()))
                return
            json_file = os.path.join(root_dir, JSON_FILE)
            try:
                fp_json = myzip.open(json_file, 'r')
            except KeyError:
                self.log.error("There is no file named '{0}' in this zip archive!".format(json_file))
                return
            json_data = json.load(fp_json)

            # check if the json is valid
            if not self.is_json_ok(data = json_data):
                return
     
            # if so, get the name of the package
            package_name = self.get_package_installation_name()
    
            # check it is not already installed
            # notice that this can't be done before as before we don't know the package name yet ;)
            if self.is_already_installed(package_name):
                return
    
            # and finally, extract the zip
            package_full = os.path.join(self.pkg_path, package_name)
            self.log.info("Extract the zip file {0} as {1}".format(path, package_full))
            try:
                os.mkdir(package_full)
            except:
                self.log.error("Error while creating the folder '{0}' : {1}".format(package_full, traceback.format_exc()))
                return
            try:
                #myzip.extractall(package_full, root_dir)


                for member in myzip.namelist():
                    member_without_parent_folder = re.sub(re.escape(root_dir), '', member)
                    filename = os.path.basename(member)
                    dirname = os.path.dirname(member_without_parent_folder)
                    # create directories
                    if not filename:
                        if dirname == "":
                            continue
                        try:
                            new_folder = os.path.join(package_full, dirname)
                            os.mkdir(new_folder)
                        except:
                            self.log.error("Error while creating the folder '{0}' : {1}".format(new_folder, traceback.format_exc()))
                            return
                        continue
                     
                    # copy file (taken from zipfile's extract)
                    source = myzip.open(member)
                    target = file(os.path.join(package_full, dirname, filename), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)


            except:
                self.log.error("Error while extracting the package in the folder '{0}' : {1}".format(package_full, traceback.format_exc()))
                return


        self.log.info("Package installed!")


    def download_from_url(self, url):
        """ Download a package from an url
        """
        try:
            self.log.info("Start downloading {0}".format(url))

            #response = requests.get(url)


            # create an empty temporary file
            downloaded_file = tempfile.NamedTemporaryFile(delete = False).name

            # process the download
            with open(downloaded_file, "wb") as f:
                response = requests.get(url, stream=STREAM)
                total_length = response.headers.get('content-length')
            
                # check the http response code
                if response.status_code != 200:
                    self.log.error("Error while downloading the package : HTTP {0}".format(response.status_code))
                    return None, None

                # check the mime type
                peek = response.iter_content(256).next()
                mime = magic.from_buffer(peek, mime=True)
                if mime not in ALLOWED_MIMES:
                    self.log.error("The package downloaded has not a compliant mime type : {0}. The mime type should be one of these : {1}".format(mime, ALLOWED_MIMES))
                    return None, None

                # download
                # if streaming is activated
                if STREAM:
                    if total_length is None: # no content length header
                        f.write(response.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        old_progress = 0
                        for data in response.iter_content(chunk_size=1024):
                            #self.log.info(dl)
                            if data:
                                f.write(data)
                                f.flush()
                                dl += len(data)
                                
                                #progress = int(50 * dl / total_length)
                                #if progress - old_progress > 5 or progress >= 49:
                                #    old_progress = progress 
                                #    sys.stdout.write("\r[%s%s]" % ('=' * progress, ' ' * (50-progress)) )    
                                #    sys.stdout.flush()
                        #sys.stdout.write("\n")
                        os.fsync(f)
                # if no streaming
                else:
                    f.write(response.content)
                    

        except: 
            self.log.error("Error while downloading the package : {0}".format(traceback.format_exc()))
        self.log.info("Download finished")
        return downloaded_file, mime

    def uninstall(self, package):
        """ Uninstall a package
            Check in /var/lib/domogik for the package
            There are 2 possibiliities :
            - the package is a symlink : just delete it
            - the package is a folder : ask before deleting it
        """
        pkg_folder = os.path.join(self.pkg_path, package)

        # check if the package is a symlink
        if os.path.islink(pkg_folder):
            # there is no need to ask the user to confirm as nothing will be lost
            try:
                os.unlink(pkg_folder)
                self.log.info("Package uninstalled from {0}".format(pkg_folder))
            except:
                self.log.error("Error while deleting symbolic link {0} : {1}".format(pkg_folder, traceback.format_exc()))

        # check if the package is a folder
        elif os.path.isdir(pkg_folder):
            # create a backup in case the user had drunk !
            self.backup(pkg_folder, os.path.join(self.pkg_path, "backup_{0}_{1}.zip".format(package, time.strftime("%Y%m%d%H%M%S")))) 
            # uninstall
            try:
                shutil.rmtree(pkg_folder)
                self.log.info("Package uninstalled from {0}".format(pkg_folder))
            except:
                self.log.error("Error while deleting folder {0} : {1}".format(pkg_folder, traceback.format_exc()))

        # not a folder, not a symlink.... not installed ?
        else:
            self.log.error("It seems that there is no such package installed")

    def list_packages(self):
        """ List installed packages and display some informations
        """

        packages = os.listdir(self.pkg_path)

        self.log.info("Domogik release : {0}".format(DMG_VERSION))
        self.log.info("")

        for a_package in packages:
            # this is a directory
            path = os.path.join(self.pkg_path, a_package)
            if os.path.isdir(path):
                self.log.info("Package {0} ".format(a_package))

                # try to load json
                self.is_json_ok(json_file = os.path.join(path, JSON_FILE))

                # display some informations
                self.log.info(" - version : {0}".format(self.json['identity']['version']))

                # installation informations
                if os.path.islink(path):
                    self.log.info(" - install mode : symbolic link to : {0}".format(os.path.realpath(path)))
                else:
                    self.log.info(" - install mode : folder")

                # add an empty line to be clearer
                self.log.info("")



    def is_json_ok(self, json_file = None, data = None):
        """ Check if the json file is OK
            @param json_file : path to the json file
            @param data : json data
        """
        try:
            if json_file != None:
                pkg_json = PackageJson(path = json_file)
            elif data != None:
                pkg_json = PackageJson(data = data)
        except:
            self.log.error(u"Error while reading the json file '{0}' : {1}".format(json_file, traceback.format_exc()))
        try:
            pkg_json.validate()
        except PackageException as e:
            self.log.error(u"Invalid json file. Reason : {0}".format(e.value))
            return False

        self.json = pkg_json.get_json()

        if self.is_compliant_with_domogik() == False:
            return False

        return True

    def get_package_installation_name(self):
        """ Return the package installation name : <type>_<name>
        """
        install_name = "{0}_{1}".format(self.json['identity']['type'], self.json['identity']['name'])
        return install_name

    def is_already_installed(self, install_name):
        """ check if it is already installed!
        """
        if os.path.isdir(os.path.join(self.pkg_path, install_name)):
            self.log.error("The package '{0}' is already installed! Please uninstall it first".format(install_name))
            return True
        return False

    def is_compliant_with_domogik(self, pkg_version = None):
        """ check if the package is compliant with the domogik installed
        """
  
        dmg_version = version.StrictVersion(DMG_VERSION)
        if pkg_version == None:
            pkg_compliant_version = version.StrictVersion(self.json['identity']['domogik_min_version'])
        else:
            pkg_compliant_version = version.StrictVersion(pkg_version)
        if pkg_compliant_version <= dmg_version:
            return True
        else:
            self.log.error("The package is not compliant with the current Domogik installation ({0}). Minimum expected version is {1}".format(DMG_VERSION, pkg_compliant_version))
            return False
        
    def backup(self, src, zip_file):
        """ Create a .zip backup of a folder
            @param src: path to save
            @param zip_file : backup
        """
        self.log.info("Creating a backup of '{0}' as '{1}'".format(src, zip_file))
        try:
            zf = zipfile.ZipFile(zip_file, "w")
            abs_src = os.path.abspath(src)
            for dirname, subdirs, files in os.walk(src):
                for filename in files:
                    absname = os.path.abspath(os.path.join(dirname, filename))
                    arcname = absname[len(abs_src) + 1:]
                    zf.write(absname, arcname)
            zf.close()
        except:
            self.log.error("Error while creating the backup : {0}".format(traceback.format_exc()))


def main():
    pkg = PackageInstaller()

if __name__ == "__main__":
    main()
