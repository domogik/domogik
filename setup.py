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


def rec_glob_get_files(path):
    d=[]
    for i in os.listdir(path):
        if not os.path.isdir(path+i):
            d.append(path+i)
        else:
            d.extend(rec_glob_get_files(path+i))
    return d

setup(
    name = 'Domogik',
    version = '0.1a',
    url = 'http://www.domogik.org/',
    author = 'OpenSource home automation software',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    install_requires=['setuptools','django >=1.1','sqlalchemy >= 0.5.4', 'simplejson >= 1.9.2'],
    zip_safe = False,
    license = 'GPL v3',
    #namespace_packages = ['domogik', 'mpris', 'tools'],
#    include_package_data = True,
    packages = find_packages('src', exclude=["mpris"]),
    package_dir = {'': 'src'},
    #Include all files of the ui/djangodomo directory
    #in data files.
    package_data = {'domogik.ui.djangodomo': rec_glob_get_files('src/domogik/ui/djangodomo/'),
        'domogik.ui.djangodomo': ['locale/*.po', 'locale/*.mo'],
                'domogik.ui.djangodomo.core': rec_glob_get_files('src/domogik/ui/djangodomo/core/templates/'),
        },
    entry_points = {
        'console_scripts': [
            """
            dmgstart = domogik.bin.dmgstart:main
            generate_config = domogik.bin.generate_config:main
            django = domogik.ui.djangodomo.manage:run_manager
            """
        ],
    },
)

