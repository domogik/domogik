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

def list_all_files(path):
    """
    List all files and subdirectories contained in a path
    @param path : the path from where to get files and subdirectories
    """
    d=[]
    for i in os.listdir(path):
        if not os.path.isdir(path+i):
            d.append(path+'/'+i)
        else:
            d.extend(list_all_files(path+'/'+i))
    return d

setup(
    name = 'Domogik',
    version = '0.1.0',
    url = 'http://www.domogik.org/',
    description = 'OpenSource home automation software',
    author = 'Domogik team',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    install_requires=['setuptools', 'django >=1.2','sqlalchemy >= 0.6.3', 'pysqlite >= 2.6.0', 'simplejson >= 1.9.2',
                      'pyOpenSSL >= 0.10', 'httplib2 >= 0.6.0', 'django-pipes >= 0.2'],
#                   deprecated, keep for info
#                   'pySerial > 2.4', 'pyowfs >= 0.1.3'],
    zip_safe = False,
    license = 'GPL v3',
    # namespace_packages = ['domogik', 'mpris', 'tools'],
    # include_package_data = True,
    packages = find_packages('src', exclude=["mpris"]),
    package_dir = {'': 'src'},
    test_suite = 'domogik.tests',
    # Include all files of the ui/djangodomo directory
    # in data files.
    package_data = {
        'domogik.ui.djangodomo': list_all_files('src/domogik/ui/djangodomo/'),
        'domogik.ui.djangodomo': ['locale/*.po', 'locale/*.mo'],
#        'domogik.ui.djangodomo.core': list_all_files('src/domogik/ui/djangodomo/core/templates/'),
    },
    data_files = [
        ('/usr/local/share/domogik/listeners/', list_all_files('src/share/domogik/stats/')),
        ('/usr/local/share/domogik/rest/', list_all_files('src/share/domogik/url2xpl/')),
        ('/usr/local/share/doc/schemas', list_all_files('src/domogik/xpl/schema/')),
        ('/usr/local/bin/', ['src/domogik/xpl/tools/xPL_Hub']),
        ('/usr/local/bin/', ['src/tools/dmgenplug']),
        ('/usr/local/bin/', ['src/tools/dmgdisplug']),
        ('/etc/init.d/', ['src/domogik/examples/init/domogik']),
        ('/etc/default/', ['src/domogik/examples/default/domogik'])
    ],

    entry_points = {
        'console_scripts': [
            """
            dmg_manager = domogik.xpl.bin.manager:main
            dmg_send = domogik.xpl.bin.send:main
            dmg_django = domogik.ui.djangodomo.manage:run_manager
            """
        ],
    },
)
