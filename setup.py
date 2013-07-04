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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ez_setup
ez_setup.use_setuptools()

import os
from setuptools import setup, find_packages
import platform

d_files = [
        ('/etc/default/', ['src/domogik/examples/default/domogik']),
        ('/etc/domogik', ['src/domogik/examples/config/domogik.cfg',  'src/domogik/examples/packages/sources.list', 'src/domogik/xplhub/examples/config/xplhub.cfg']),
        ('/var/cache/domogik', []),
        ('/var/cache/domogik/pkg-cache', []),
        ('/var/cache/domogik/cache', []),
        ('/var/lib/domogik', []),
        ('/var/lib/domogik/packages', ['src/domogik/common/__init__.py']),
        ('/var/lib/domogik/resources', []),
        ('/var/lib/domogik/resources', ['src/domogik/common/datatypes.json']),
        ('/var/lock/domogik', []),
]

if os.path.exists('/etc/default'):
    d_files.append(('/etc/default/', ['src/domogik/examples/default/domogik']))
else:
    print "Can't find directory where i can copy system wide config"
    exit(0)

if os.path.exists('/etc/logrotate.d'):
    d_files.append(('/etc/logrotate.d', ['src/domogik/examples/logrotate/domogik', 'src/domogik/xplhub/examples/logrotate/xplhub']))

if os.path.exists('/etc/init.d'):
    d_files.append(('/etc/init.d/', ['src/domogik/examples/init/domogik']))
elif os.path.exists('/etc/rc.d'):
    d_files.append(('/etc/rc.d/', ['src/domogik/examples/init/domogik']))
else:
    print("Can't find firectory for init script")
    exit(0)

def get_path(dir_only=False):
    arch = platform.machine()
    hub = {
        'x86_64' : 'src/domogik/xpl/tools/64bit/',
        'i686' : 'src/domogik/xpl/tools/32bit/',
        'arm' : 'src/domogik/xpl/tools/arm/',
        'armv5tel' : 'src/domogik/xpl/tools/arm/',
        'armv6l' : 'src/domogik/xpl/tools/arm/'
    }
    if arch not in hub.keys():
        return None
    else:
        if not dir_only:
            return hub[arch] + "xPL_Hub"
        else:
            return hub[arch]

arch = get_path()
if arch != None:
    d_files.append(('/usr/sbin/', [arch]))
else:
    print("*************** WARNING ***************")
    print("* Can't find an xPL Hub for your arch *")
    print("* Please check documentation in :     *")
    print("*  src/domogik/xpl/tools/COMPILE.txt  *")
    print("* to get the sources and compile them.*")
    print("***************************************")

setup(
    name = 'Domogik',
    version = '0.4.0',
    url = 'http://www.domogik.org/',
    description = 'OpenSource home automation software',
    author = 'Domogik team',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    install_requires=['setuptools', 
                      'sqlalchemy == 0.7.9',
                      'sqlalchemy-migrate >= 0.7.2',
                      'simplejson >= 1.9.2',
                      'pyOpenSSL >= 0.10', 
                      'httplib2 >= 0.6.0', 
                      'psutil >= 0.1.3', 
                      'MySQL-python >= 1.2.3c', 
                      'pyinotify >= 0.8.9', 
                      'pip >= 1.0', 
                      'Distutils2',
                      'pyserial >= 2.5',
                      'netifaces >= 0.8',
                      'Twisted >= 12.1.0',
                      'Flask >= 0.9',
                      'tornado >= 3.1',
                      'pyzmq >= 13.1.0',
                      'python-daemon >= 1.5.5'],
    zip_safe = False,
    license = 'GPL v3',
    include_package_data = True,
    packages = find_packages('src/domogik'),
    package_dir = { 
        '': 'src/domogik'
    },
    test_suite = 'domogik.tests',
    package_data = {
        'domogik': [
            #'examples/config/domogik.cfg',
            'examples/init/domogik',
            'examples/default/domogik',
            'examples/logrotate/domogik',
            'examples/snmp/snmp.cfg',
            'examples/snmp/dmg_snmp',
            'examples/snmp/dmg_snmp.pl',
            'install/uninstall.sh',
            'install/version',
            'common/datatypes.json',
            'install/upgrade_repository/migrate.cfg',
            'install/upgrade_repository/versions/*',
            'xplhub/examples/logrotate/xplhub',
            'xplhub/examples/config/xplhub.cfg',
            'xpl/tools/32bit/xPL_Hub',
            'xpl/tools/64bit/xPL_Hub',
            'xpl/tools/arm/xPL_Hub',
        ]
    },
    data_files = d_files,
    scripts=['install.sh', 'test_config.py'],
    entry_points = {
        'console_scripts': [
            """
            dmg_pkgmgr = domogik.xpl.bin.pkgmgr:main
            dmg_manager = domogik.xpl.bin.manager:main
            dmg_send = domogik.xpl.bin.send:main
            dmg_dump = domogik.xpl.bin.dump_xpl:main
            dmg_mq_dump = domogik.mq.dump:main
            dmg_version = domogik.xpl.bin.version:main
            dmg_hub = domogik.xpl.bin.hub:main
            dmg_broker = domogik.mq.reqrep.broker:main
            dmg_forwarder = domogik.mq.pubsub.forwarder:main
            dmg_insert_data = domogik.tools.packages.insert_data:main
            dmg_review = domogik.tools.packages.review.review:main
            """
        ],
    },
    classifiers=[
        "Topic :: Home Automation",
        "Environment :: No Input/Output (Daemon)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
    ]
)
