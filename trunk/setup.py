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

res = rec_glob_get_files('domogik/ui/')
print res
setup(
    name = 'Domogik',
    version = '0.1a',
    url = 'http://www.domogik.org/',
    author = 'OpenSource home automation software',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    packages=find_packages(),
    package_dir = {'domogik':'domogik'},
#    namespace_packages=['domogik',],
    install_requires=['setuptools','django >=1.0'],
    zip_safe = False,
    license = 'GPL v3',
    scripts = ['domogik/bin/generate_config.py','domogik/bin/dmgstart.py'],
    package_data = {'domogik':res},
    )

