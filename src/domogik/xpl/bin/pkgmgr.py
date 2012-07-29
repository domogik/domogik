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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
from domogik.common.packagemanager import PackageManager
from domogik.common.packagexml import PackageXml, PackageException
from domogik.common.packagejson import set_nightly_version
from optparse import OptionParser

PACKAGE_TYPES = ['plugin', 'external']
    
def main():
    mgr = PackageManager()

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
    #parser.add_option("-i", "--install",
    #                  action = "store_true", 
    #                  dest = "action_install",
    #                  default = False,
    #                  help = "Install a package (<package> [version])")
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
    #parser.add_option("-s", "--show",
    #                  action = "store_true", 
    #                  dest = "action_show",
    #                  default = False,
    #                  help = "Display cache's package list")
    parser.add_option("-t", "--type",
                      action = "store", 
                      dest = "package_type",
                      help = "Package type : %s" % PACKAGE_TYPES)
    parser.add_option("-o", "--output-dir",
                      action = "store", 
                      dest = "output_dir",
                      help = "Directory where you want to create packages")
    parser.add_option("-n", "--nightly",
                      action = "store_true", 
                      dest = "action_nightly",
                      default = False,
                      help = "Change the version in json file for nightly build")
    parser.add_option("-j", "--to-json",
                      action = "store_true", 
                      dest = "action_json",
                      default = False,
                      help = "Convert the xml to json (temporary option for 0.2.0 development)")
    parser.add_option("-V", "--version",
                      action="store_true",
                      dest="display_version",
                      default=False,
                      help="Display Domogik version.")

    
    (options, args) = parser.parse_args()
    
    if options.display_version:
        __import__("domogik")
        global_release = sys.modules["domogik"].__version__
        print global_release
        return

    # check args
    if (options.action_update == False \
            and options.action_list == False )\
            and len(args) < 1:
        parser.print_help()
        exit()
      
    # package creation
    if options.action_create == True:
        # check package type
        if options.package_type not in PACKAGE_TYPES:
            print("Error : : type must be in this list : %s" % PACKAGE_TYPES)
            exit()
    
        # plugin
        if options.package_type == "plugin":
            mgr._create_package_for_plugin(args[0], options.output_dir, options.force)
        # external
        if options.package_type == "external":
            mgr._create_package_for_external(args[0], options.output_dir, options.force)
    
    # package installation
    #if options.action_install == True:
    #    if len(args) == 1:
    #        mgr.install_package(args[0])
    #    if len(args) == 2:
    #        mgr.install_package(args[0], args[1])
    
    # packages list update
    if options.action_update == True:
        mgr.update_cache()
    
    # list packages in cache
    if options.action_list == True:
        mgr.list_packages()
    
    # show packages in cache
    #if options.action_show == True:
    #    if len(args) == 1:
    #        mgr.show_packages(args[0])
    #    if len(args) == 2:
    #        mgr.show_packages(args[0], args[1])

    if options.action_json == True:
        if options.package_type not in PACKAGE_TYPES:
            print("Error : : type must be in this list : %s" % PACKAGE_TYPES)
            exit()
        pkg_xml = PackageXml(args[0], pkg_type = options.package_type)
        print (pkg_xml.get_json())

    if options.action_nightly == True:
        set_nightly_version(args[0])

    
if __name__ == "__main__":
    main()
