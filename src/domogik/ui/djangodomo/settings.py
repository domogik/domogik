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



Implements
==========


@author: Marc Schneider <marc@mirelsol.org>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
from domogik.common.configloader import Loader

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Note that we use our own Database model and not Django's one.

### Rest settings
cfg_rest = Loader('django')
config_django = cfg_rest.load()
conf_django = dict(config_django[1])

if ('internal_rest_server_ip' in conf_django) and (conf_django['internal_rest_server_ip'] != ''):
    INTERNAL_REST_IP = conf_django['internal_rest_server_ip']
else:    # default parameters
    INTERNAL_REST_IP = "127.0.0.1"

if ('internal_rest_server_port' in conf_django) and (conf_django['internal_rest_server_port'] != ''):
    INTERNAL_REST_PORT = conf_django['internal_rest_server_port']
else:
    # default parameters
    INTERNAL_REST_PORT = "8080"

if ('internal_rest_server_prefix' in conf_django) and (conf_django['internal_rest_server_prefix'] != ''):
    INTERNAL_REST_PREFIX = conf_django['internal_rest_server_prefix']
    INTERNAL_REST_URL = "http://" + INTERNAL_REST_IP + ":" + INTERNAL_REST_PORT + "/" + INTERNAL_REST_PREFIX
else:
    INTERNAL_REST_URL = "http://" + INTERNAL_REST_IP + ":" + INTERNAL_REST_PORT

if ('external_rest_server_ip' in conf_django) and (conf_django['external_rest_server_ip'] != ''):
    EXTERNAL_REST_IP = conf_django['external_rest_server_ip']
else:
    # default parameters
    EXTERNAL_REST_IP = INTERNAL_REST_IP

if ('external_rest_server_port' in conf_django) and (conf_django['external_rest_server_port'] != ''):
    EXTERNAL_REST_PORT = conf_django['external_rest_server_port']
else:
    # default parameters
    EXTERNAL_REST_PORT = INTERNAL_REST_PORT

if ('external_rest_server_prefix' in conf_django) and (conf_django['external_rest_server_prefix'] != ''):
    EXTERNAL_REST_PREFIX = conf_django['external_rest_server_prefix']
    EXTERNAL_REST_URL = "http://" + EXTERNAL_REST_IP + ":" + EXTERNAL_REST_PORT + "/" + EXTERNAL_REST_PREFIX
else:
    EXTERNAL_REST_URL = "http://" + EXTERNAL_REST_IP + ":" + EXTERNAL_REST_PORT

print "DJANGO REST url : " + INTERNAL_REST_URL
print "JQUERY REST url : " + EXTERNAL_REST_URL


PROXY_DOMAIN = INTERNAL_REST_IP
PROXY_PORT = int(INTERNAL_REST_PORT)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'i#=g$uo$$qn&0qtz!sbimt%#d+lb!stt#12hr@%vp-u)yw3s+b'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    # TODO : uncomment this once multi-languages will be supported
    # 'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'domogik.ui.djangodomo.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '%s/home/templates/' % PROJECT_PATH,
    '%s/view/templates/' % PROJECT_PATH,
    '%s/admin/templates/' % PROJECT_PATH,
    '%s/rinor/templates/' % PROJECT_PATH,
    '/usr/local/share/domogik/ui/djangodomo/home/templates/',
    '/usr/local/share/domogik/ui/djangodomo/view/templates/',
    '/usr/local/share/domogik/ui/djangodomo/admin/templates/',
    '/usr/local/share/domogik/ui/djangodomo/rinor/templates/',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_pipes', # Used to create Django's model using REST
    'domogik.ui.djangodomo.home',
    'domogik.ui.djangodomo.view',
    'domogik.ui.djangodomo.admin',
    'domogik.ui.djangodomo.rinor',
)


# Session stuff
# Other options are :
### 'django.contrib.sessions.backends.db'
### 'django.contrib.sessions.backends.file'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

PIPES_CACHE_EXPIRY=1

try:
    from settings_local import *
except ImportError:
    pass

# List the availables widgets
WIDGETS_LIST = []
STATIC_WIDGETS_ROOT = None
#STATIC_DESIGN_ROOT = None 

#Only loads the widgets from the FIRST existing directory in TEMPLATE_DIRS
for t_path in (PROJECT_PATH, '/usr/local/share/domogik/ui/djangodomo/',):
    if os.path.isdir(t_path):
        STATIC_DESIGN_ROOT = '%s/design' % t_path
        w_path = os.path.join(t_path, "widgets")
        STATIC_WIDGETS_ROOT = w_path
        if os.path.isdir(w_path):
            for file in os.listdir(w_path):
                main = os.path.join(w_path, file, "main.js")
                if os.path.isfile(main):
                    WIDGETS_LIST.append(file)
        break


# For login Auth
AUTHENTICATION_BACKENDS = ('domogik.ui.djangodomo.backends.RestBackend',)
LOGIN_URL = '/admin/login'
LOGOUT_URL = '/admin/logout'
LOGIN_REDIRECT_URL = '/admin/'
