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


urlpatterns = patterns('domogik.ui.djangodomo.admin.views',
    url(r'login/$', 'login', name='login_view'),
    url(r'logout/$', 'logout', name='logout_view'),

    url(r'^$', 'admin_organization_house', name="admin_index_view"),
    url(r'management/accounts/$', 'admin_management_accounts', name="admin_management_accounts_view"),
    url(r'organization/$', 'admin_organization_house', name="admin_organization_view"),
    url(r'organization/house/$', 'admin_organization_house', name="admin_organization_view_house_view"),
    url(r'organization/areas/$', 'admin_organization_areas', name="admin_organization_areas_view"),
    url(r'organization/rooms/$', 'admin_organization_rooms', name="admin_organization_rooms_view"),
    url(r'organization/devices/$', 'admin_organization_devices', name="admin_organization_devices_view"),
    url(r'organization/widgets/$', 'admin_organization_widgets', name="admin_organization_widgets_view"),
    url(r'plugin/(?P<plugin_host>[a-zA-Z0-9_.-]+)/(?P<plugin_name>\w+)/(?P<plugin_type>\w+)/$', 'admin_plugins_plugin', name="admin_plugins_plugin_view"),
    url(r'tools/helpers/$', 'admin_tools_helpers', name="admin_tools_helpers_view"),
    url(r'tools/rinor/$', 'admin_tools_rinor', name="admin_tools_rinor_view"),
    url(r'packages/repositories/$', 'admin_packages_repositories', name="admin_packages_repositories_view"),
    url(r'packages/plugins/$', 'admin_packages_plugins', name="admin_packages_plugins_view"),
    url(r'packages/hardwares/$', 'admin_packages_hardwares', name="admin_packages_hardwares_view"),
    url(r'packages/install/(?P<package_host>[a-zA-Z0-9_.-]+)/(?P<package_name>[a-zA-Z0-9_.-]+)/(?P<package_release>[a-zA-Z0-9_.-]+)/$', 'admin_packages_install', name="admin_packages_install_view"),
    url(r'packages/enable/(?P<package_host>[a-zA-Z0-9_.-]+)/(?P<package_name>[a-zA-Z0-9_.-]+)/(?P<action>\w+)/$', 'admin_packages_enable', name="admin_packages_enable_view"),
)
