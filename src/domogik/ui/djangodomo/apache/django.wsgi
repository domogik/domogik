#!/usr/bin/python2.6
import os
import sys
import site
sys.stdout = sys.stderr
site.addsitedir('/usr/local/lib/python2.6/dist-packages')
os.environ['DJANGO_SETTINGS_MODULE'] = 'domogik.ui.djangodomo.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
