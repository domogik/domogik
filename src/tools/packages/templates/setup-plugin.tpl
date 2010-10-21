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

Help to manage Domogik plugins installation

Implements
==========


@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ez_setup
ez_setup.use_setuptools()

import os
from setuptools import setup, find_packages

def list_all_files(path, dst):
    """
    List all files and subdirectories contained in a path
    @param path : the path from where to get files and subdirectories
    @param dst : The based destination path
    @return : a list of tuples for each directory in path (including path itself)
    """
    d = []
    files = []
    try:
        for i in os.listdir(path):
            if not os.path.isdir(os.path.join(path, i)):
                files.append(os.path.join(path, i))
            else:
                d.extend(list_all_files(os.path.join(path, i), os.path.join(dst, i)))
    except OSError:
        return []
    d.append((dst, files))
    return d


d_files = []

d_files.extend(list_all_files('src/share/domogik/stats/', '/usr/local/share/domogik/listeners/'))
d_files.extend(list_all_files('src/share/domogik/url2xpl/', '/usr/local/share/domogik/url2xpl/'))
d_files.extend(list_all_files('src/share/domogik/plugins/', '/usr/local/share/domogik/plugins/'))

print d_files
setup(
    name = '%name%',
    version = '%version%',
    url = '%doc%',
    description = '%desc%',
    author = '%author%',
    author_email = '%email%',
    install_requires=[%depandancies%],
    zip_safe = False,
    license = 'GPL v3',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    data_files = d_files,
)
