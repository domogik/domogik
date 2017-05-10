#!/usr/bin/env python
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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ez_setup
ez_setup.use_setuptools()

import os
from setuptools import setup, find_packages
import platform
import sys

if sys.version_info[0] == 3:
    netifaces = 'netifaces-py3'
else:
    netifaces = 'netifaces'

pyzmq_found = False
mysql = 'pymysql'
magic = 'python-magic >= 0.4.3'

import pip
for mod in pip.get_installed_distributions():
    if ( mod.key == 'mysql-python' ):
        mysql = 'mysql-python'
    if ( mod.key == 'magic-file-extensions' ):
        magic = 'magic-file-extensions'
    if ( mod.key == 'pyzmq' ):
        pyzmq_found = True

print "******************************************"
print "use: "+mysql
print "use: "+magic
print "******************************************"

setup(
    name = 'Domogik',
    version = '0.6.0',
    url = 'http://www.domogik.org/',
    description = 'OpenSource home automation software',
    author = 'Domogik team',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    install_requires=['setuptools',
          ],
    zip_safe = False,
    license = 'GPL v3',
    #include_package_data = True,
    packages = find_packages('src', exclude=["mpris"]),
    package_dir = { '': 'src' },
    test_suite = 'domogik.tests',
    package_data = {},
    scripts=[],
    entry_points = {
        'console_scripts': [
        """
            dmg_manager = domogik.bin.manager:main
            dmg_send = domogik.bin.send:main
            dmg_dump = domogik.bin.dump_xpl:main
            dmg_version = domogik.bin.version:main
            dmg_hub = domogik.bin.hub:main
            dmg_package = domogik.bin.package:main
            dmg_testrunner = domogik.tests.bin.testrunner:main
            dmg_cron = domogik.bin.cron:main
        """
        ]
    },
    classifiers=[
        "Topic :: Home Automation",
        "Environment :: No Input/Output (Daemon)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English"
    ]
)

