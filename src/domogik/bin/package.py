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

from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.xpl.common.plugin import PACKAGES_DIR
from domogik.common.packagejson import PackageJson, PackageException
from argparse import ArgumentParser
import re
import os
import traceback
import zipfile
import json
import shutil

JSON_FILE = "info.json"

class PackageInstaller():
    """ Package installer class
    """
    def __init__(self):
        """ Init
        """
        l = logger.Logger("package")
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
        self.pkg_path = "{0}/{1}".format(conf['libraries_path'], PACKAGES_DIR)

        # install a package
        if self.options.install:
            self.install(self.options.install)
 
        # uninstall a package
        if self.options.uninstall:
            self.uninstall(self.options.uninstall)


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

        # check if the package is a zip file
        elif zipfile.is_zipfile(package):
            self.install_zip_file(package)

        # the package format is not handled
        else:
            self.log.error("This tool doesn't handle this kind of package")
   

        # TODO : finish

    def install_folder(self, path):
        """ Install the package from a folder
            If there is a correst json file, just create a symlink :)
        """
        self.log.info("Install a package from a folder : {0}".format(path))
        # check if there is the json file
        json_file = "{0}/{1}".format(path, JSON_FILE)
        if not os.path.isfile(json_file):
            self.log.error("There is no json file in this folder : {0}".format(json_file))
            return

        # check if the json file is valid
        if not self.is_json_ok(json_file = json_file):
            return

        # if so, get the name of the package (symlink name)
        symlink_name = self.get_package_installation_name()

        # check it is not already installed
        if self.is_already_installed(symlink_name):
            return

        # and finally, create the symlink
        symlink_full = "{0}/{1}".format(self.pkg_path, symlink_name)
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
            json_file = "{0}{1}".format(root_dir, JSON_FILE)
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
            if self.is_already_installed(package_name):
                return
    
            # and finally, extract the zip
            package_full = "{0}/{1}".format(self.pkg_path, package_name)
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
                            new_folder = "{0}/{1}".format(package_full, dirname)
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


    def uninstall(self, package):
        """ Uninstall a package
            Check in /var/lib/domogik for the package
            There are 2 possibiliities :
            - the package is a symlink : just delete it
            - the package is a folder : ask before deleting it
        """
        # TODO
        print "@@@ TODO @@@"

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

        # TODO : check package is compliant with domogik
        return True

    def get_package_installation_name(self):
        """ Return the package installation name : <type>_<name>
        """
        install_name = "{0}_{1}".format(self.json['identity']['type'], self.json['identity']['name'])
        return install_name

    def is_already_installed(self, install_name):
        """ check if it is already installed!
        """
        if os.path.isdir("{0}/{1}".format(self.pkg_path, install_name)):
            self.log.error("The package '{0}' is already installed! Please uninstall it first".format(install_name))
            return True
        return False



def main():
    pkg = PackageInstaller()

if __name__ == "__main__":
    main()
