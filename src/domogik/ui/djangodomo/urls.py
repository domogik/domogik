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


@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', include('domogik.ui.djangodomo.home.urls')),
    (r'^view/', include('domogik.ui.djangodomo.view.urls')),
    (r'^admin/', include('domogik.ui.djangodomo.admin.urls')),
    (r'^rinor/', include('domogik.ui.djangodomo.rinor.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #(r'^admin/', include(admin.site.urls)),
    # TODO : change this, only used in development environment
    # See : http://docs.djangoproject.com/en/dev/howto/static-files/
    (r'^design/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DESIGN_ROOT}),
    (r'^widgets/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_WIDGETS_ROOT}),
)

