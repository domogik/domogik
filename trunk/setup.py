#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name = 'Domogik',
    version = '0.1a',
    url = 'http://www.domogik.org/',
    author = 'OpenSource home automation software',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    package_dir = {'': 'domogik'},
    packages=find_packages('domogik'),
#    namespace_packages=['domogik',],
    include_package_data = True,
    install_requires=['setuptools','django'],
    zip_safe = False,
    license = 'GPL v3',
    )
