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


urlpatterns = patterns('domogik.ui.djangodomo.view.views',
    url(r'^$', 'house', name="view_index_view"),
    url(r'house/$', 'house', name="view_house_view"),
    url(r'house/edit/(?P<from_page>\w+)/$', 'house_edit', name="edit_house_view"),
    url(r'area/(?P<area_id>\d+)/$', 'area', name='view_area_view'),
    url(r'area/edit/(?P<area_id>\d+)/(?P<from_page>\w+)/$', 'area_edit', name='edit_area_view'),
    url(r'room/(?P<room_id>\d+)/$', 'room', name='view_room_view'),
    url(r'room/edit/(?P<room_id>\d+)/(?P<from_page>\w+)/$', 'room_edit', name='edit_room_view')
)
