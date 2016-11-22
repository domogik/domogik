from better import better_theme_path
import sys
import os

extensions = [
    'sphinx.ext.todo',
]

source_suffix = '.txt'

master_doc = 'index'

project = u'Domogik'
copyright = u'2015, Domogik'
version = ''
release = version

pygments_style = 'sphinx'

#html_theme = 'default'

# sphinx-better-theme
html_theme_path = [better_theme_path]
html_theme = 'better'

html_static_path = ['_static']
htmlhelp_basename = project

