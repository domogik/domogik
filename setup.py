#!/usr/bin/python

#Prepare env for using setuptools
import ez_setup
ez_setup.use_setuptools()

#Main install part
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
    install_requires=['setuptools','django >=1.0'],
    zip_safe = False,
    license = 'GPL v3',
    namespace_packages = ['domogik', 'mpris', 'tools'],
    include_package_data = True,
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    extras_require={'test': ['IPython', 'zope.testing',]},
    data_files = [
        ('domogik', rec_glob_get_files('src/domogik/ui/')),
    ],
    entry_points = {
        'console_scripts': [
            """
            dmgstart = domogik.bin.dmgstart:main
            generate_config = domogik.bin.generate_config:main
            """
        ],
    },
)

