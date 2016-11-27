#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Diagnostic script for Domogik
#


# TODO :
# - magic utf8 thing in header
# - no (" but only (u" 
# - no while.*true
# - no doc error

import tempfile
import traceback
import os
import sys
import json
import struct
import subprocess
import re

FILE=os.path.join(tempfile.gettempdir(), "pkg_review.log")
# TODO : improve to find it dynamically
DMG_SRC="/opt/dmg/domogik/"


class Review():

    def __init__(self, pkg_dir):
        self.is_warning = False
        self.is_error = False
    
        self.pkg_dir = pkg_dir
        self.info("Package location : {0}".format(pkg_dir))

        self.title("Read the json file")
        # Load json
        self.load_json()

        ### Basic informations
        self.read_identity()

        ### Technic informations
        self.is_xpl = None
        self.is_xpl_plugin()

        ### Tests
        self.title("Check important files")
        self.has_automated_tests = None
        self.has_icon = None
        self.check_important_files()

        ### Code
        self.title("Code quality")
        self.python_bad_usages()

        ### Design
        self.title("Design items")
        self.check_design()

        ### Doc
        self.title("Documentation")
        self.doc_url_root = self.build_doc_url()
        self.doc_url_en_version = self.build_doc_url("en", self.pkg_version)
        #self.doc_url_fr_version = self.build_doc_url("fr", self.pkg_version)
        #self.build_doc()
        
    
        ### Summary
        self.title("Summary")

        if self.is_warning:
            print(u"There were some warnings !")
        if self.is_error:
            print(u"There were some errors !")
        if not self.is_warning and not self.is_error:
            print(u"All seems OK")

        self.title("Manual TODO list")

        self.action("Design : check the icon appearance")
        self.action("Battery : check if the plugin manager sensors about batteries. If so, check that the appropriate DT_Battery is used.")
        self.action("Motion : check if the plugin manager sensors about motion sensors. If so, check that the appropriate DT_Motion is used.")

        if self.has_automated_tests:
            self.action("Automated test : check they run")
            self.action("Automated test : check travis is configured and passed!")
        else:
            self.action("Check if some tests are described in the doc")

        self.action("Doc : '{0}' is linked to the last version ({1})".format(self.doc_url_root, self.pkg_version))
        self.action("Doc : '{0}' is ok and up to date".format(self.doc_url_en_version, self.pkg_version))

    # LOG FUNCTIONS
    #######################################################################################################
    
    def title(self, msg):
        print(u"")
        print(u"===========================================================")
        print(u"   {0}".format(msg))
        print(u"===========================================================")
        print(u"")
    
    def action(self, msg):
        print(u"ok[ ]  ko[ ]  n/a[ ] : {0}".format(msg))
    
    def ok(self, msg):
        print(u"OK       : {0}".format(msg))
    
    def info(self, msg):
        print(u"INFO     : {0}".format(msg))
    
    def warning(self, msg):
        print(u"WARNING  : {0}".format(msg))
        self.is_warning = True
    
    def error(self, msg):
        print(u"ERROR    : {0}".format(msg))
        self.is_error = True
    
    def solution(self, msg):
        print(u"SOLUTION : {0}".format(msg))
    
    
    # Json checks
    #######################################################################################################
    
    def load_json(self):
        try:
            self.json_data = json.load(open(os.path.join(self.pkg_dir, "info.json")))
        except:
            self.error("Unable to read the 'info.json' file as a Json file! Error is : {0}".format(traceback.format_exc()))

    def read_identity(self):
        try:
            self.pkg_type = self.json_data["identity"]["type"]
            self.pkg_name = self.json_data["identity"]["name"]
            self.pkg_version = self.json_data["identity"]["version"]
            self.pkg_domogik_min_version = self.json_data["identity"]["domogik_min_version"]
            self.pkg_author = self.json_data["identity"]["author"]
            self.pkg_author_email = self.json_data["identity"]["author_email"]
        except:
            self.error("Unable to read some 'info.json' identity informations! Error is : {0}".format(traceback.format_exc()))

        self.info("Package type                : {0}".format(self.pkg_type))
        self.info("Package name                : {0}".format(self.pkg_name))
        self.info("Package version             : {0}".format(self.pkg_version))
        self.info("Package domogik min version : {0}".format(self.pkg_domogik_min_version))
        self.info("Package author              : {0}".format(self.pkg_author))
        self.info("Package author email        : {0}".format(self.pkg_author_email))

    
    def is_xpl_plugin(self):
        try:
            self.xpl_cmds = self.json_data["xpl_commands"]
            self.xpl_stats = self.json_data["xpl_stats"]
            if self.xpl_cmds == {} and self.xpl_stats == {}:
                self.info("This is NOT a xPL plugin")
                self.is_xpl = False
            else:
                self.info("This is a xPL plugin : there are some xpl commands or xpl stats defined")
                self.warning("Depending on the plugin, you may consider to convert it to a non xPL plugin!")
                self.is_xpl = True
        except:
            self.error("Unable to read some 'info.json' xpl informations! Error is : {0}".format(traceback.format_exc()))


    # Files checks
    #######################################################################################################
    
    def check_important_files(self):
        # git related
        self.check_file_exists(".gitignore")
    
        # all packages related
        self.check_file_exists("__init__.py")

        # plugin only related
        if self.pkg_type == "plugin":
            self.check_file_exists("bin/__init__.py")
            self.check_file_exists("lib/__init__.py")
        # brain only related
        if self.pkg_type == "brain":
            self.check_file_exists("rs/fr_FR")
            self.check_file_exists("rs/en_EN")
            self.check_file_exists("rs/en_US")
            self.check_file_exists("rs/nl_NL")
    
        # license related
        self.check_file_exists("LICENSE")
        self.check_file_exists("COPYING")
    
        # doc related
        self.check_file_exists("README.md")
        self.check_file_exists("CHANGELOG")
        self.check_file_exists("docs/index.txt")
        self.check_file_exists("docs/{0}.txt".format(self.pkg_name))
        self.check_file_exists("docs/changelog.txt")
    
        # icon related
        self.has_icon = self.check_file_exists("design/icon.png")
    
        # tests related
        self.has_automated_tests = self.check_file_exists("tests/tests.json")
        
    
    def check_file_exists(self, filename):
        if not os.path.isfile(os.path.join(self.pkg_dir, filename)):
            self.error("A file is missing : '{0}'".format(filename))
            return False
        else:
            self.info("File present : '{0}'".format(filename))
            return True
    
    # Design
    #######################################################################################################
    
    def check_design(self):
        h, w = self.get_image_size(os.path.join(self.pkg_dir, "design/icon.png"))
        if h != 96 or w != 96:
            self.error("The icon is not in the required size : {0}x{1} instead of 96x96".format(h,w))
        else:
            self.info("Icon size OK : 96x96")

    def get_image_size(self, file_path):
        """
        Return (width, height) for a given img file content - no external
        dependencies except the os and struct modules from core
        """
        size = os.path.getsize(file_path)
    
        with open(file_path) as input:
            height = -1
            width = -1
            data = input.read(25)
    
            if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
                # GIFs
                w, h = struct.unpack("<HH", data[6:10])
                width = int(w)
                height = int(h)
            elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
                  and (data[12:16] == 'IHDR')):
                # PNGs
                w, h = struct.unpack(">LL", data[16:24])
                width = int(w)
                height = int(h)
            elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
                # older PNGs?
                w, h = struct.unpack(">LL", data[8:16])
                width = int(w)
                height = int(h)
            elif (size >= 2) and data.startswith('\377\330'):
                # JPEG
                msg = " raised while trying to decode as JPEG."
                input.seek(0)
                input.read(2)
                b = input.read(1)
                try:
                    while (b and ord(b) != 0xDA):
                        while (ord(b) != 0xFF): b = input.read(1)
                        while (ord(b) == 0xFF): b = input.read(1)
                        if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                            input.read(3)
                            h, w = struct.unpack(">HH", input.read(4))
                            break
                        else:
                            input.read(int(struct.unpack(">H", input.read(2))[0])-2)
                        b = input.read(1)
                    width = int(w)
                    height = int(h)
                except struct.error:
                    raise UnknownImageFormat("StructError" + msg)
                except ValueError:
                    raise UnknownImageFormat("ValueError" + msg)
                except Exception as e:
                    raise UnknownImageFormat(e.__class__.__name__ + msg)
            else:
                raise UnknownImageFormat(
                    "Sorry, don't know how to get information from this file."
                )
    
        return width, height


    # Docs
    #######################################################################################################

    def build_doc_url(self, lang = "", version = ""):
        url = "http://domogik-{0}-{1}.readthedocs.org".format(self.pkg_type, self.pkg_name)
        if lang != "":
            url += "/en"
        if version != "":
            url += "/{0}".format(version)
        return url
    
    def build_doc(self):

        conf_py = os.path.join(DMG_SRC, "docs")
        build_doc_dir = os.path.join("/tmp", "dmg_builddoc_{0}_{1}".format(self.pkg_type, self.pkg_name))
        makefile = os.path.join(DMG_SRC, "docs/Makefile")
        # -e if used to use environments vars
        cmd = "cd {0} && export BUILDDIR={1} && export SPHINXOPTS='-c {2}' && make -e -f {3} html".format(os.path.join(self.pkg_dir, "docs"), build_doc_dir, conf_py, makefile)
        subp = subprocess.Popen(cmd,
                     shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = subp.communicate()

        if  subp.returncode == 0:
            self.info("The doc has compiled successfully")
        else:
            self.error("Error on compiling the doc.\n\nSTDOUT : \n{0}\n\nSTDERR :\n{1}\n\n".format(result[0], result[1]))
            return
    

    # Code
    #######################################################################################################

    def python_bad_usages(self):
        """ Check in the python code for some bad usages
        """
        the_files = []
        for r,d,f in os.walk(self.pkg_dir):
            for files in f:
                if files.endswith(".py"):
                     the_files += [os.path.join(r,files)]

        # Do the "while True" check for each file
        # while *True must not be used as this is blocking for stopping the plugin properly
        self._python_find_bad_usages("Avoid while True loops", "while *True", the_files)
        self._python_find_bad_usages("Avoid direct reference to /tmp (use the tempfile library instead)", "/tmp", the_files)
        self._python_find_bad_usages("Avoid direct reference to /var/lib/domogik/... (use the Plugin functions instead)", "/var/lib/domogik", the_files)

    def _python_find_bad_usages(self, explanation, pattern, file_list):
        """ Look for a bad pattern in a list of files
        """
        for the_file in file_list:
            found_bad_usage, bad_usages =  self._grep(the_file, pattern)
            if found_bad_usage:
                self.warning(u"Bad usage detected in the file '{0}' : {1}".format(the_file, explanation))
                for line in bad_usages:
                    print(u"{0}".format(line.strip()))

    def _grep(self, filename, pattern):
        """ search for the pattern in the file
        """
        lines_found = []
        found = False
        line_num = 0
        for line in open(filename):
            line_num += 1
            if re.search(pattern, line):
                found = True
                lines_found.append("%4d:%s" % (line_num, line))
        return found, lines_found



    
class UnknownImageFormat(Exception):
    pass



# LAUNCH TESTS
#######################################################################################################

if __name__ == "__main__":
    # Folder
    pkg_dir = sys.argv[1]
    R = Review(pkg_dir)

