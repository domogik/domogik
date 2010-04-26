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
from djangodomo.core.models import DeviceTypes, DeviceUsages

register = template.Library()

class GetCommandBinary(Node):
    _dict = None
    def __init__(self, feature):
        self.feature = template.Variable(feature)

    def render(self, context):
        feature = self.feature.resolve(context)
        device_type = DeviceTypes.get_dict_item(feature.device.device_type_id)
        device_usage = DeviceUsages.get_dict_item(feature.device.device_usage_id)
        script = """var parameters_type = $.getJson('%s');
                    var parameters_usage = $.getJson('%s');
                    
                    $('#command_%s_%s').binary_command({
                        usage: %s,
                        value0: parameters_type.value0,
                        value1: parameters_type.value1,
                        text0: parameters_usage.binary.state0,
                        text1: parameters_usage.binary.state1,
                        action: function(self, value) {
                            $.getREST(['command', '%s', '%s', value],
                                function(data) {
                                    var status = (data.status).toLowerCase();
                                    if (status == 'ok') {
                                        self.valid(%s);
                                    } else {
                                        /* Error */
                                        self.cancel();
                                    }
                                }
                            );
                        }
                    })
                        .binary_command('setState', 'Off');
                    """ % (feature.device_type_feature.parameters, device_usage.default_options, feature.device_id, feature.device_type_feature_id, feature.device.device_usage_id, device_type.device_technology_id, feature.device.address, feature.device_type_feature.return_confirmation)
        return script

class GetCommandRange(Node):
    _dict = None
    def __init__(self, feature):
        self.feature = template.Variable(feature)

    def render(self, context):
        feature = self.feature.resolve(context)
        device_type = DeviceTypes.get_dict_item(feature.device.device_type_id)
        device_usage = DeviceUsages.get_dict_item(feature.device.device_usage_id)
        script = """var parameters_type = $.getJson('%s');
                    var parameters_usage = $.getJson('%s');
                    $("#command_%s_%s").range_command({
                        usage: %s,
                        min_value: parameters_type.valueMin,
                        max_value: parameters_type.valueMax,
                        step: parameters_usage.range.step,
                        unit: parameters_usage.range.unit,
                        action: function(self, value) {
                            $.getREST(['command', '%s', '%s', parameters_type.command, value],
                                function(data) {
                                    var status = (data.status).toLowerCase();
                                    if (status == 'ok') {
                                        self.valid(%s);
                                    } else {
                                        /* Error */
                                        self.cancel();
                                    }
                                }
                            );
                        }
                    })
                        .range_command('setValue', 50);
                    """ % (feature.device_type_feature.parameters, device_usage.default_options, feature.device_id, feature.device_type_feature_id, feature.device.device_usage_id, device_type.device_technology_id, feature.device.address, feature.device_type_feature.return_confirmation)
        return script
    
def do_get_command_binary(parser, token):
    """
    This returns the jquery function for creating a binary command.

    Usage::

        {% get_command_binary feature %}
    """
    args = token.contents.split()
    if len(args) != 2:
        raise TemplateSyntaxError, "'get_command_binary' requires 'feature' argument"
    return GetCommandBinary(args[1])

register.tag('get_command_binary', do_get_command_binary)

def do_get_command_range(parser, token):
    """
    This returns the jquery function for creating a range command.

    Usage::

        {% get_command_range feature %}
    """
    args = token.contents.split()
    if len(args) != 2:
        raise TemplateSyntaxError, "'get_command_range' requires 'feature' argument"
    return GetCommandRange(args[1])

register.tag('get_command_range', do_get_command_range)
