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
import re

ALL_REPO = "@@ALL@@"   # string to identify a better repo than stable (used for self._no_more)
REPO_STABLE = "stable"    
REPO_TESTING = "testing"
REPO_EXPERIMENTAL = "experimental"
REPO_LIST = ['experimental', 'testing', 'stable', ALL_REPO] # the better last
                                                            # the last one must be ALL_REPO
REPO_NB = len(REPO_LIST)-1
REVIEW_DIR = "/tmp/dmg_review"
DOC_OUTPUT = "%s/doc-build.log" % REVIEW_DIR
DOC_BUILD = "file://%s/docs/_build/html/index.html" % REVIEW_DIR
ICON = "%s/icon.png" % REVIEW_DIR
ICON_FORMAT = "PNG"
ICON_SIZE = (96, 96)
SRC_DIR = "%s/src" % REVIEW_DIR

LINE_SEPARATOR = "============================================================================"
LINE_BLANK = "                 "

#PD = PackageData(sys.argv[1])
#PD.insert()



class PkgReview:

    def __init__(self, path):
        """ Review a package
        """
        self._path = path

        ### candidates
        # self.candidates contains the values (True/False) for the REPO_LIST
        self.candidates = []
        # Set all the repo as candidates in the beginning
        for idx in range(0, len(REPO_LIST)):
            self.candidates.append(True)

        ### Check for blocking points
        # If these points are not ok, the package can't be reviewed

        # check the package format
        self.title("Check the package format")
        self._check_format()
        self._extract()

        ### Check all other points
        # files between sources and the package 
        # check if all in included
        self._included_files()

        # doc
        self.title("Documentation review")
        self._compile_doc()
        self._review_doc()
        self._review_wiki_doc()

        # icon
        self.title("Icon review")
        self._review_icon()

        # json
        # - version
        # - online versions (all)
        # - contact and email
        # - domogik min version

        # python
        self.title("Python code : quality analysis")
        self._pylint()
        self._python_bad_usages()

        # web pages ?
        self.title("Domoweb related pages")
        self._domoweb()

        # tests 
        self.title("Tests review")
        self._review_test()

        ### The end
        self.title("Review finished!")
        # find the winner
        for idx in range(len(REPO_LIST)-1, -1, -1):
            if self.candidates[idx] == True:
                break
        print("The package can be pushed on the '%s' repository!!" % REPO_LIST[idx])




    #### log/report functions ####

    def title(self, msg):
        """ title
           @param msg : message to display
        """
        print("\n%s" % LINE_SEPARATOR)
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
           @param repo : repo which will be refused because of the error : REPO_STABLE, REPO_TESTING, ....
        """
        print("[ ERROR        ] %s" % msg)
        self._no_more(repo)
        
    def critical(self, msg):
        """ Critical error. Display the message and quit
        """
        print("[ CRITICAL     ] %s" % msg)
        sys.exit(1)

    def ask_boolean(self, msg):
        """ ask  a question for the user. Returns "y" or "n"
           @param msg : message to display
        """
        print("[ MANUAL CHECK ] %s" % msg)
        rep = 'x'
        # the user will just answer yes or no
        while rep not in ['y', 'n']:
            rep = raw_input("%s[y/n] > " % LINE_BLANK)
        return rep
    
    def ask(self, msg, repo = None):
        """ ask a manuel check by the user
           @param msg : message to display
           @param repo : if != None : repo which will be refused because of the error : REPO_STABLE, REPO_TESTING, ....
                         if None : the candidate repo will be asked to the user
        """
        print("[ MANUAL CHECK ] %s" % msg)
        rep = 'x'
        # the user will just answer yes or no
        if repo != None:
            while rep not in ['y', 'n']:
                rep = raw_input("%sIs this ok ? [y/n] > " % LINE_BLANK)
            if rep == 'n':
                self._no_more(repo)

        # the user will have to choose the repo
        else:
            while rep not in REPO_LIST:
                rep = raw_input("%sFor which repo is this valid ? %s > " % (LINE_BLANK, REPO_LIST[0:REPO_NB]))
            # we remove the next repo in the list (the one better than the choosen one)
            self._no_more(REPO_LIST[1+REPO_LIST.index(rep)])
        return rep
    

    def _no_more(self, repo):
        """ set the package 'no more' candidate for a repo
           @param repo : repo name
        """
        if repo != ALL_REPO:
            self.warning("The '%s' repository is no more candidate because of this error" % repo)
            for idx in range(REPO_LIST.index(repo), len(REPO_LIST)):
                self.candidates[idx] = False
        
        
    


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
        self.debug("Compile the doc...")
        cmd = "cd %s/docs && make html" % REVIEW_DIR
        p_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_cmd.wait()

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
            self.error("Error on compiling the doc. See %s" % DOC_OUTPUT, REPO_TESTING)
            return

    def _review_doc(self):
        """ Check the doc
            This is actually a dedicated function in case of futur automated tests
        """
        self.ask("Please check the doc compilation output : %s" % DOC_OUTPUT, REPO_TESTING)
        doc_build_checklist = "Please check the html doc build in your browser : %s" % DOC_BUILD
        doc_build_checklist += "\n%s- The package description is fine" % LINE_BLANK
        doc_build_checklist += "\n%s- There is a picture/photography to illustrate the package" % LINE_BLANK
        doc_build_checklist += "\n%s- There is no more TODO" % LINE_BLANK
        doc_build_checklist += "\n%s- There is no syntax or grammar error" % LINE_BLANK
        doc_build_checklist += "\n%s- There is (if needed) a helper page" % LINE_BLANK
        doc_build_checklist += "\n%s- There is (if needed) a page for domoweb special pages" % LINE_BLANK
        self.ask(doc_build_checklist, REPO_TESTING)

    def _review_wiki_doc(self):
        """ Check the wiki doc
        """
        wiki_check_list = "Please check the doc on the wiki : http://wiki.domogik.org/plugin_XXXX"
        wiki_check_list += "\n%s- There is no more 'user doc' in the wiki, just dev notes or specs" % LINE_BLANK
        wiki_check_list += "\n%s- There is a link on the wiki to this package doc (nightly release)" % LINE_BLANK
        wiki_check_list += "\n%s- There is no more link to the wiki page on http://wiki.domogik.org/Plugins_in_Domogik" % LINE_BLANK
        wiki_check_list += "\n%s- This plugin json key for doc is linked to the wiki page and not the package doc" % LINE_BLANK
        self.ask(wiki_check_list, REPO_TESTING)

    def _review_icon(self):
        """ Check the icon
            - format
            - size
        """
        im = Image.open(ICON)

        # check the format
        self.debug("Icon format : %s" % str(im.format)) 
        if im.format != ICON_FORMAT:
            self.error("The icon format is not good : %s instead of %s" % (im.format, ICON_FORMAT), REPO_STABLE)
        else:
            self.ok("The icon format is OK : %s" % ICON_FORMAT)

        # check the size
        self.debug("Icon size : %s" % str(im.size)) 
        if im.size != ICON_SIZE:
            self.error("The icon size is not good : %s instead of %s" % (im.size, ICON_SIZE), REPO_STABLE)
        else:
            self.ok("The icon size is OK : %s" % str(ICON_SIZE))




    def _included_files(self):
        """ Ask the user to check if all the files are included in the package
        """
        files_checklist = "All the files below are the only ones needed by the package (please compare to the sources) :"
        for r,d,f in os.walk(REVIEW_DIR):
            for files in f:
                if files not in ['_theme', '_build']:
                    if "_theme" not in r.split("/") and \
                       "_build" not in r.split("/"):
                        files_checklist += "\n%s- %s" % (LINE_BLANK, os.path.join(r,files))
        self.ask(files_checklist, REPO_TESTING)
        



    def _pylint(self):
        """ Launch pylint on each python file
        """
        # Just list the files
        the_files = []
        self.debug("List the python files to analysis...")
        for r,d,f in os.walk(SRC_DIR):
            for files in f:
                if files.endswith(".py"):
                     self.debug("- %s" %  os.path.join(r,files))
                     the_files += [os.path.join(r,files)]

        # Do the pylint check for each file
        for the_file in the_files:
            # file for stdout & stderr
            pylint_out = "%s.pylint" % the_file

            ### launch pylint and get the output
            self.info("Analysing %s..." % the_file)
            cmd = "pylint %s" % the_file
            p_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p_cmd.wait()

            # write the output in the DOC_OUTPUT file
            # and get the code rating
            doc_file = open(pylint_out,'w')
    
            doc_file.write("%s\n" % LINE_SEPARATOR)
            doc_file.write("Stderr\n")
            doc_file.write("%s\n" % LINE_SEPARATOR)
            for line in iter(p_cmd.stderr.readline, ''):
                doc_file.write(line)
    
            doc_file.write("\n\n\n%s\n" % LINE_SEPARATOR)
            doc_file.write("Stdout\n")
            doc_file.write("%s\n" % LINE_SEPARATOR)
            the_score = 0
            for line in iter(p_cmd.stdout.readline, ''):
                doc_file.write(line)
                # Intercept the code rating
                if line[0:9] == "Your code":
                    the_score = float(line[28:].split("/")[0])
    
            self.info("- Analysis done. The result is in %s" % pylint_out)
            self.info("- The code rating is %.2f/10" % the_score)
            # if the score is greater than 8, we assume that the quality is enough for going in the stable repo
            # but if this is not the case, we ask the user to read the output (pylint may give some bad score for
            # some bad reasons)
            if the_score >= 8:
                self.ok("- The code quality is good for this file : more than 8/10")
            else:
                self.ask("Please look at pylint output to choose the best candidate repository for this file")

    def _python_bad_usages(self):
        """ Check in the python code for some bad usages
        """
        the_files = []
        self.debug("List the python files to analysis...")
        for r,d,f in os.walk(SRC_DIR):
            for files in f:
                if files.endswith(".py"):
                     self.debug("- %s" %  os.path.join(r,files))
                     the_files += [os.path.join(r,files)]

        # Do the "while True" check for each file
        # while *True must not be used as this is blocking for stopping the plugin properly
        self._python_find_bad_usages("while *True", the_files)
        

    def _python_find_bad_usages(self, pattern, file_list):
        """ Look for a bad pattern in a list of files
        """
        for the_file in file_list:
            found_bad_usage, bad_usages =  self._grep(the_file, pattern)
            if found_bad_usage:
                result = "\n"
                for line in bad_usages:
                    result += "%s%s" % (LINE_BLANK, line)
                self.warning("There may be something bad in : %s%s" % (the_file, result))
                self.ask("Check in the file if this is OK")






    def _domoweb(self):
        """ Ask the user some questions about Domoweb related pages
        """
        rep = self.ask_boolean("Is there any special pages in Domoweb related to this package ?")
        # no special pages, no more questions
        if rep == 'n':
            return

        # ask the suer to do some checks
        domoweb_checklist = "Please check the special pages on the actual domoweb stable release"
        domoweb_checklist += "\n%s- The current Domoweb stable release contains all the needed pages for this package release" % LINE_BLANK
        domoweb_checklist += "\n%s- This package version will work perfectly with the Domoweb special pages" % LINE_BLANK
        self.ask(domoweb_checklist, REPO_STABLE)

    def _review_test(self):
        """ Ask the user some questions about the tests
        """
        msg = "Test cases and test campaign are managed on http://test.domogik.org/"
        msg += "\n%sIf you don't have any account, juste send an email to the developpers mailing list"
        self.info(msg)
        rep = self.ask("Some test cases are defined for this package release.", REPO_TESTING)
        if rep == "n":
            return
        rep = self.ask("A test campaign has been defined and the more important features has been tested.", REPO_TESTING)
        if rep == "n":
            return
        rep = self.ask("A test campaign has been defined and all the tests are OK.", REPO_STABLE)
        if rep == "n":
            return











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

if __name__ == "__main__":
    review = PkgReview(sys.argv[1])

