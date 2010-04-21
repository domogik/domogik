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


@author: Domogik project
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from django import template
from django.template import Node
from djangodomo.core.models import DeviceTypes

register = template.Library()

class DeviceType(Node):
    _dict = None
    def __init__(self, id, variable):
        self.id = template.Variable(id)
        self.variable = variable

    def render(self, context):
        if DeviceType._dict is None:
            print "device types downloading"
            types = DeviceTypes.get_all()
            DeviceType._dict = {}
            for type in types.device_type:
                DeviceType._dict[type.id] = type
        else:
            print "device types already downloaded"
        id = self.id.resolve(context)
        context[self.variable] = DeviceType._dict[id]
        return ''
    
def do_get_device_type(parser, token):
    """
    This generate the javascript command button script.

    Usage::

        {% get_device_type device_id as variable%}
    """
    args = token.contents.split()
    if len(args) != 4:
        raise TemplateSyntaxError, "'get_device_type' requires 'id' and 'as variable' arguments"
    return DeviceType(args[1], args[3])

register.tag('get_device_type', do_get_device_type)
