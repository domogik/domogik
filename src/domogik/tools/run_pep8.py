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

Module purpose
==============

Check PEP 8

Implements
==========

- main()

@author: Domogik project
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import pep8
from os.path import abspath, dirname


class options:
    filename = ["*.py"]
    exclude = ".hg"
    verbose = False
    counters = {}
    messages = {}
    testsuite = False
    quiet = False
    ignore = []
    repeat = False
    show_source = True
    show_pep8 = False


def main():
    """
    Parse options and run checks on Python source.
    """
    pep8.options = options()
    repo = dirname(dirname(abspath(__file__)))
    pep8.input_dir(repo)


if __name__ == '__main__':
    main()
