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

This library is part of the butler

Implements
==========


@author: Fritz SMH <fritz.smh at gmail.com>
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.butler.brain import get_resources_directory
import json
import traceback
import time
import os

class ItemList:

    def __init__(self, log, tag):
        # log
        self.log = log
        # load the appropriate list
        res_dir = get_resources_directory()
        self.path = os.path.join(res_dir, "butler", "{0}.json".format(tag))
        self.log.debug("ItemList : storage file is '{0}'".format(self.path))
        self.data = None
        self._load_json()

        # special case : empty list
        if self.data == None:
            self._init_json()

    def _load_json(self):
        # open
        try:
            with open(self.path) as jsonfp:
                self.data = json.load(jsonfp)
            self.log.debug("File '{0}' loaded. Content is : '{1}'".format(self.path, self.data))
        except IOError, e:
            if e.errno == 2:
                self.log.info("The file self.path does not exist yet")
            else:
                self.log.error("Error while loading file '{0}' : {1}".format(self.path, traceback.format_exc()))
        except:
            self.log.error("Error while loading file '{0}' : {1}".format(self.path, traceback.format_exc()))

        # some checks about the format
        invalid = False
        if self.data != None:
            for key in ['last_update', 'list']:
                if key not in self.data:
                    self.log.error("Json in bad format : key '{0}' not present".format(key))
                    invalid = True
        if invalid:
           self.log.error("Invalid json format => data set to null")
           self.data = None

    def _init_json(self):
        self.data = {'last_update' : None,
                     'list' : []
                    }

    def _save_json(self):
        self.log.debug("Save JSON")
        self.data['last_update'] = time.time()
        self.log.debug(self.data)
        try:
            with open(self.path, "w") as fp:
                json.dump(self.data, fp)
        except:
            self.log.error("Error while saving file '{0}'. Error is: {1}".format(self.path, traceback.format_exc()))

    def add(self, item):
        """
            @return : status (boolean), reason code
        """
        self.log.debug("Add : {0}".format(item))
        ### check if already present in the list
        # simple check
        if item in self.data['list']:
            return False, "ALREADY_IN_LIST"
 
        # more complex check
        # TODO

        # add in list
        self.data['list'].append(item.strip())
        self._save_json()
        return True, None

    def remove(self, item):
        """
            @return : status (boolean), reason code
        """
        self.log.debug("Remove : {0}".format(item))
        ### check if present in the list
        # simple check
        if item not in self.data['list']:
            return False, "NOT_IN_LIST"
 
        # more complex check
        # TODO

        # remove from list
        self.data['list'].remove(item.strip())
        self._save_json()
        return True, None

    def clean(self):
        """
            @return : status (boolean), reason code
        """
        self.log.debug("Clean the list")

        # clean list
        self.data['list'] = []
        self._save_json()
        return True, None

    def get_as_list(self):
        self.log.debug("Get list of items")
        return self.data['list']

    def generate_postscript(self, title):
        """ Generate postscript data to print the list
        """
        # Postscript header
        data = ""
        data += "%!PS-Adobe-2.0\n"
        data += "%%Creator: someone@somewhere\n"
        data += "%%EndComments\n"
        data += "/mainfont /Courier findfont 12 scalefont def\n"
        data += "mainfont setfont\n"
        data += "%%EndProlog\n"
        data += "%%Page: ? 1\n"

        # Title
        yy = 790
        data += "40 {0} moveto\n".format(yy)
        data += "({0}) show\n".format(title)
        yy -= 10

        # Add the items
        for item in self.get_as_list():
            # TODO: security if yy < 0
            yy -= 20
            data += "60 {0} moveto\n".format(yy)
            data += "({0}) show\n".format(item)
            data += "newpath\n"
            data += "40 {0} moveto\n".format(yy)
            data += "0 6 rlineto\n"
            data += "6 0 rlineto\n"
            data += "0 -6 rlineto\n"
            data += "-6 0 rlineto\n"
            data += "1 setlinewidth\n"
            data += "closepath\n"
            data += "stroke\n"
            data += "stroke\n"

        # Postscript Footer
        data += "showpage\n"
        data += "%%Pages: 1\n"

        print(data)
        return data

class Log:
    def __init__(self):
        pass
    
    def info(self, msg):
        print(msg)
    
    def debug(self, msg):
        print(msg)
    
    def warning(self, msg):
        print(msg)
    
    def error(self, msg):
        print(msg)

if __name__ == "__main__":
    c = ItemList(Log(), "foo")
    print(c.add(" tutu  "))
    print(c.get_as_list())
    print(c.add("tutu"))
    print(c.add("bar"))
    print(c.get_as_list())
    print(c.remove("barzz"))
    print(c.get_as_list())
    print(c.remove("bar"))
    print(c.get_as_list())

