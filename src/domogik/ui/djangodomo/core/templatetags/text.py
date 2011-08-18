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

register = template.Library()

@register.filter
# truncate after a certain number of characters
def truncchar(value, arg):
    if len(value) < arg:
        return value
    else:
        return value[:arg] + '.'

@register.filter
def switchUnderscore(value):
    return value.replace('_', ' ')

class GetPosition(Node):
    def __init__(self, array, id, grouper):
        self.array = template.Variable(array)
        self.id = template.Variable(id)
        self.grouper = template.Variable(grouper)

    def render(self, context):
        res = 0
        array = self.array.resolve(context)
        id = self.id.resolve(context)
        grouper = self.grouper.resolve(context)
        for i in range(len(array)):
            if grouper == 1:
                if array[i]['grouper'].id == id:
                    res = i                
            else:
                if array[i].id == id:
                    res = i
        return res
    
def do_get_position(parser, token):
    """
    This returns the position.

    Usage::

        {% get_position array id grouper %}
    """
    args = token.contents.split()
    if len(args) != 4:
        raise TemplateSyntaxError, "'get_position' requires arguments"
    return GetPosition(args[1], args[2], args[3])

register.tag('get_position', do_get_position)