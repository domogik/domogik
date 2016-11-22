# -*- coding: utf-8 -*-
#

import sys, os

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinxcontrib.blockdiag', 'sphinxcontrib.nwdiag', 'sphinxcontrib.seqdiag', 'sphinxcontrib.actdiag']
#templates_path = ['_templates']
source_suffix = '.txt'
master_doc = 'contents'

# General information about the project.
project = u'Domogik'
copyright = u'2016, Domogik'

version = '0.5'
release = '0.5'

exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos=True

html_theme_path = [better_theme_path]
html_theme = 'better'
html_static_path = []


latex_elements = {
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'Domogik.tex', u'Domogik Documentation',
   u'Domogik team', 'manual'),
]

man_pages = [
    ('index', 'domogik', u'Domogik Documentation',
     [u'Domogik team'], 1)
]

texinfo_documents = [
  ('index', 'Domogik', u'Domogik Documentation',
   u'Domogik team', 'Domogik', 'One line description of project.',
   'Miscellaneous'),
]

