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

Help to manage Domogik installation

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
from install.get_arch import *
import platform

def list_all_files(path, dst):
    """
    List all files and subdirectories contained in a path
    @param path : the path from where to get files and subdirectories
    @param dst : The based destination path
    @return : a list of tuples for each directory in path (including path itself)
    """
    d = []
    files = []
    for i in os.listdir(path):
        if not os.path.isdir(os.path.join(path, i)):
            files.append(os.path.join(path, i))
        else:
            d.extend(list_all_files(os.path.join(path, i), os.path.join(dst, i)))
    d.append((dst, files))
    return d

arch = get_path()

d_files = [
        ('/usr/local/bin/', ['src/tools/dmgenplug']),
        ('/usr/local/bin/', ['src/tools/dmgdisplug']),
        ('/etc/init.d/', ['src/domogik/examples/init/domogik']),
        ('/etc/default/', ['src/domogik/examples/default/domogik'])
]

if arch != None:
    d_files.append(('/usr/local/bin/', [arch]))
else:
    print "*************** WARNING ***************"
    print "* Can't find an xPL Hub for your arch *"
    print "* Please check documentation in :     *"
    print "*  src/domogik/xpl/tools/COMPILE.txt  *"
    print "* to get the sources and compile them.*"
    print "***************************************"

#d_files.extend(list_all_files('src/share/domogik/stats/', '/usr/local/share/domogik/stats/'))
#d_files.extend(list_all_files('src/share/domogik/url2xpl/', '/usr/local/share/domogik/url2xpl/'))
#d_files.extend(list_all_files('src/share/domogik/plugins/', '/usr/local/share/domogik/plugins/'))

setup(
    name = 'Domogik',
    version = '0.2.0',
    url = 'http://www.domogik.org/',
    description = 'OpenSource home automation software',
    author = 'Domogik team',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    install_requires=['setuptools', 
                      'sqlalchemy == 0.7.5',
                      'sqlalchemy-migrate >= 0.7.2',
                      'simplejson >= 1.9.2',
                      'pyOpenSSL >= 0.10', 
                      'httplib2 >= 0.6.0', 
                      'psutil >= 0.1.3', 
                      'MySQL-python >= 1.2.3c', 
                      'pyinotify >= 0.8.9', 
                      'pip >= 1.0', 
                      'Distutils2',
                      'pyserial >= 2.5'],
    zip_safe = False,
    license = 'GPL v3',
    # namespace_packages = ['domogik', 'mpris', 'tools'],
    # include_package_data = True,
    packages = find_packages('src', exclude=["mpris"]),
    package_dir = {'': 'src'},
    test_suite = 'domogik.tests',
    package_data = {
    },
    data_files = d_files,

    entry_points = {
        'console_scripts': [
            """
            dmg_pkgmgr = domogik.xpl.bin.pkgmgr:main
            dmg_manager = domogik.xpl.bin.manager:main
            dmg_send = domogik.xpl.bin.send:main
            dmg_version = domogik.xpl.bin.version:main
            """
        ],
    },
)
