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

Command line tool for validating a plugin json

Implements
==========

- PluginJsonValidator

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.packagejson import PackageJson, PackageException
from argparse import ArgumentParser

class PluginJsonValidator():
    """ Plugin validator command line tool
    """
    def __init__(self):
        """ Init
        """
        parser = ArgumentParser()
        parser.add_argument("path", 
                          help="Path to the json file")
        self.options = parser.parse_args()

        if self.options.path != '':
            try:
                pkg = PackageJson(path=self.options.path)
                pkg.validate()
                print("JSON OK")
            except PackageException as e:
                print("JSON NOT OK")
                print(e.value)
        else:
            parser.print_help()


def main():
    pkg = PluginJsonValidator()

if __name__ == "__main__":
    main()
