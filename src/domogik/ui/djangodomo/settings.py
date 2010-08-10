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

#DATABASE_ENGINE = 'mysql'   # 'postgresql_psycopg2', 'postgresql', 'mysql',
                            # 'sqlite3' or 'oracle'.
#DATABASE_NAME = 'domogik'   # Or path to database file if using sqlite3.

#DATABASE_ENGINE = 'sqlite3'
#DATABASE_NAME = "db.sqlite"

#DATABASE_USER = 'domogik'   # Not used with sqlite3.
#DATABASE_PASSWORD = ''      # Not used with sqlite3.
#DATABASE_HOST = ''          # Set to empty string for localhost.
                            # ( Not used with sqlite3. )
#DATABASE_PORT = ''          # Set to empty string for default.
                            # ( Not used with sqlite3. )

DATABASES = {
    'default': {
        'NAME': 'db.sqlite',
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': '',
        'PASSWORD': '',
    }
}

### Proxy settings
try:
    cfg_rest = Loader('django')
    config_django = cfg_rest.load()
    conf_django = dict(config_django[1])
    REST_IP = conf_django['django_rest_server_ip']
    REST_PORT = conf_django['django_rest_server_port']
    REST_PREFIX = conf_django['django_rest_server_prefix']
    if ('django_rest_server_prefix' in conf_django) and (conf_django['django_rest_server_prefix'] != ''): 
        REST_PREFIX = conf_django['django_rest_server_prefix']
        REST_URL = "http://" + REST_IP + ":" + REST_PORT + "/" + REST_PREFIX
    else: 
        REST_PREFIX = ''
        REST_URL = "http://" + REST_IP + ":" + REST_PORT

except KeyError:
    # default parameters
    REST_IP = "127.0.0.1"
    REST_PORT = "8080"
    REST_PREFIX = ''
    REST_URL = "http://" + REST_IP + ":" + REST_PORT

print "using REST url : " + REST_URL

PROXY_DOMAIN = REST_IP
PROXY_PORT = int(REST_PORT)

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
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'domogik.ui.djangodomo.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '%s/templates/' % PROJECT_PATH,
    '%s/core/templates/' % PROJECT_PATH,
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
    'django_pipes',
    'domogik.ui.djangodomo.core',
)

STATIC_DESIGN_ROOT = '%s/core/templates/design' % PROJECT_PATH
STATIC_WIDGETS_ROOT = '%s/core/templates/widgets' % PROJECT_PATH

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
WIDGETS_PATH = '%s/core/templates/widgets/' % PROJECT_PATH
WIDGETS_LIST = []
for file in os.listdir(WIDGETS_PATH):
    main = os.path.join(WIDGETS_PATH, file, "main.js")
    if os.path.isfile(main):
        WIDGETS_LIST.append(file)
