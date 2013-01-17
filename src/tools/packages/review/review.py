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

Review a package

Implements
==========

PkgReview

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


#from domogik.common.packagedata import PackageData
import os
import sys
import shutil
import mimetypes
import traceback
import tarfile
import subprocess
import time
from PIL import Image

REVIEW_DIR = "/tmp/dmg_review"
DOC_OUTPUT = "%s/doc-build.log" % REVIEW_DIR
DOC_BUILD = "file://%s/docs/_build/html/index.html" % REVIEW_DIR
ICON = "%s/icon.png" % REVIEW_DIR
ICON_FORMAT = "PNG"
ICON_SIZE = (96, 96)

LINE_SEPARATOR = "============================================================================"
LINE_BLANK = "                 "

#PD = PackageData(sys.argv[1])
#PD.insert()



class PkgReview:

    def __init__(self, path):
        """ Review a package
        """
        self._path = path

        ### flags
        self.stable = True       # can the package be pushed in stable ?
        self.testing = True      # can the package be pushed in testing ?
        self.experimental = True # can the package be pushed in experimental ?

        ### Check for blocking points
        # If these points are not ok, the package can't be reviewed

        # check the package format
        self.title("Check the package format")
        self._check_format()
        self._extract()

        ### Check all other points
        # doc
        #self.title("Documentation review")
        #self._compile_doc()
        #self._review_doc()

        # icon
        self.title("Icon review")
        self._review_icon()

        # json
        # - version
        # - online versions (all)
        # - contact and email
        # - domogik min version

        # python
        # - file names
        # - pylint

        # web pages ?

        # tests ?



        ### The end
        self.title("Review finished!")
        if self.stable:
            winner = "Stable"
        elif self.testing:
            winner = "Testing"
        elif self.experimental:
            winner = "Experimental"
        print("The package can be pushed on the '%s' repository!!" % winner)




    #### log/report functions ####

    def title(self, msg):
        """ title
           @param msg : message to display
        """
        print(LINE_SEPARATOR)
        print("%s" % msg)
        print(LINE_SEPARATOR)
        
    def debug(self, msg):
        """ debug
           @param msg : message to display
        """
        print("[ DEBUG        ] %s" % msg)
        
    def info(self, msg):
        """ info
           @param msg : message to display
        """
        print("[ INFO         ] %s" % msg)
        
    def ok(self, msg):
        """ ok
           @param msg : message to display
        """
        print("[ OK           ] %s" % msg)
        
    def warning(self, msg):
        """ warning
           @param msg : message to display
        """
        print("[ WARNING      ] %s" % msg)
        
    def error(self, msg, repo):
        """ error
           @param msg : message to display
           @param repo : repo which will be refused because of the error : stable, testing, experimental
        """
        print("[ ERROR        ] %s" % msg)
        self._no_more(repo)
        
    def critical(self, msg):
        """ Critical error. Display the message and quit
        """
        print("[ CRITICAL     ] %s" % msg)
        sys.exit(1)

    def ask(self, msg, repo):
        """ ask a manuel check by the user
           @param msg : message to display
           @param repo : repo which will be refused because of the error : stable, testing, experimental
        """
        print("[ MANUAL CHECK ] %s" % msg)
        rep = 'x'
        while rep not in ['y', 'n']:
            rep = raw_input("%sIs this ok ? [y/n] > " % LINE_BLANK)
        if rep == 'n':
            self._no_more(repo)
    

    def _no_more(self, repo):
        """ set the package 'no more' candidate for a repo
           @param repo : repo name
        """
        self.info("The '%s' repository is no more candidate because of this error" % repo)
        if repo in ['experimental']:
            self.experimental = False
            self.testing = False
            self.stable = False
        if repo in ['testing']:
            self.testing = False
            self.stable = False
        if repo in ['stable']:
            self.stable = False
        
        
    


    #### review functions ####

    def _check_format(self):
        """ Check if this is a valid tgz
            Check the package name
            Check the version in the package name
        """
        # check the mimetype
        mtype, entype = mimetypes.guess_type(self._path)
        if mtype != "application/x-tar":           
            self.critical("The mimetype is not application/x-tar : %s" % mtype)
        if entype != "gzip": 
            self.critical("The entype is not gzip : %s" % entype)
        self.ok("The mimetype is OK")


    def _extract(self):
        """ Extract the package in the REVIEW_DIR 
            - clean the REVIEW_DIR
            - extract
        """
        # create the folder (even if it exists)
        self._create_folder(REVIEW_DIR)
        # clean the folder (in case it already exists)
        self._clean_folder(REVIEW_DIR)
        # extract the package
        self._extract_package(self._path, REVIEW_DIR)


    def _compile_doc(self):
        """ Compile the package doc and check for errors
        """
        #self.debug("Go in the doc folder...")
        #cmd = "cd %s/docs" % REVIEW_DIR
        #p_cmd = subprocess.Popen(cmd, shell=True)
        #p_cmd.communicate()
        #if  p_cmd.returncode == 0:
        #    self.debug("...OK")
        #else:
        #    self.error("No doc folder found", "testing")
        #    return

        self.debug("Compile the doc...")
        cmd = "cd %s/docs && make html" % REVIEW_DIR
        p_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #p_cmd.wait()

        # write the output in the DOC_OUTPUT file
        doc_file = open(DOC_OUTPUT,'w')

        doc_file.write("%s\n" % LINE_SEPARATOR)
        doc_file.write("Stderr\n")
        doc_file.write("%s\n" % LINE_SEPARATOR)
        for line in iter(p_cmd.stderr.readline, ''):
            doc_file.write(line)

        doc_file.write("\n\n\n%s\n" % LINE_SEPARATOR)
        doc_file.write("Stdout\n")
        doc_file.write("%s\n" % LINE_SEPARATOR)
        for line in iter(p_cmd.stdout.readline, ''):
            doc_file.write(line)

        if  p_cmd.returncode == 0:
            self.debug("...OK")
            self.ok("The doc has compiled successfully")
        else:
            self.error("Error on compiling the doc. See %s" % DOC_OUTPUT, "testing")
            return

    def _review_doc(self):
        """ Check the doc
            This is actually a dedicated function in case of futur automated tests
        """
        self.ask("Please check the doc compilation output : %s" % DOC_OUTPUT, "testing")
        doc_build_checklist = "Please check the html doc build in your browser : %s" % DOC_BUILD
        doc_build_checklist += "\n%s- Package description is fine" % LINE_BLANK
        self.ask(doc_build_checklist, "testing")

    def _review_icon(self):
        """ Check the icon
            - format
            - size
        """
        im = Image.open(ICON)

        # check the format
        self.debug("Icon format : %s" % str(im.format)) 
        if im.format != ICON_FORMAT:
            self.error("The icon format is not good : %s instead of %s" % (im.format, ICON_FORMAT), "stable")
        else:
            self.ok("The icon format is OK : %s" % ICON_FORMAT)

        # check the size
        self.debug("Icon size : %s" % str(im.size)) 
        if im.size != ICON_SIZE:
            self.error("The icon size is not good : %s instead of %s" % (im.size, ICON_SIZE), "stable")
        else:
            self.ok("The icon size is OK : %s" % ICON_SIZE)







    #### All the following functions are utilities ####

    def _create_folder(self, folder):
        """ Try to create a folder (does nothing if it already exists)
            @param folder : folder path
        """
        try:
            if os.path.isdir(folder) == False:
                self.debug("Creating directory : %s" % folder)
                os.makedirs(folder)
        except:
            msg = "Error while creating temporary folder '%s' : %s" % (folder, traceback.format_exc())
            self.critical(msg)

    def _clean_folder(self, folder):
        """ Delete the content of a folder
            @param folder: folder to clean
        """
        # Clean folder
        self.debug("Clean the folder : %s" % folder)
        try:
            for root, dirs, files in os.walk(folder):
                for fic in files:
                    os.unlink(os.path.join(root, fic))
                for dir in dirs:
                    shutil.rmtree(os.path.join(root, dir))
        except:
            msg = "Error while cleaning cache folder '%s' : %s" % (folder, traceback.format_exc())
            self.critical(msg)
            raise PackageException(msg)

    def _extract_package(self, pkg_path, extract_path):
        """ Extract package <pkg_path> in <extract_path>
            @param pkg_path : path to package
            @param extract_path : path for extraction
        """
        tar = tarfile.open(pkg_path)
        # check if there is no .. or / in files path
        self.debug("Extracting package...")
        for fic in tar.getnames():
            if fic[0:1] == "/" or fic[0:2] == "..":
                msg = "Error while extracting package '%s' : filename '%s' in tgz not allowed" % (pkg_path, fic)
                self.critical(msg)
                raise PackageException(msg)
        tar.extractall(path = extract_path)
        tar.close()


if __name__ == "__main__":
    review = PkgReview(sys.argv[1])

