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
from domogik.ui.djangodomo.core.models import DeviceTypes, DeviceUsages, Stats
from htmlentitydefs import name2codepoint
import re
import simplejson

register = template.Library()

def unescape(s):
    "unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
    return re.sub('&(%s);' % '|'.join(name2codepoint),
              lambda m: unichr(name2codepoint[m.group(1)]), s)

class GetCommandBinary(Node):
    @staticmethod
    def get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage):
        script = """$('#widget_%s_%s').widget_mini_command_binary({
                        usage: %s,
                        devicename: '%s',
                        featurename: '%s',
                        value0: '%s',
                        value1: '%s',
                        text0: '%s',
                        text1: '%s',
                        action: function(self, values) {
                            $.getREST(['command', '%s', '%s', values.value],
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
                    });
                    """ % (feature.device_id, feature.device_feature_id, feature.device.device_usage_id,
                           feature.device.name, feature.device_feature.name,
                           parameters_type['value0'], parameters_type['value1'],
                           parameters_usage['binary']['state0'], parameters_usage['binary']['state1'],
                           device_type.device_technology_id, feature.device.address, feature.device_feature.return_confirmation)
        return script

    @staticmethod
    def get_setValue(feature, value):
        script = """$("#widget_%s_%s").widget_mini_command_binary('setValue', %s);
                    """ % (feature.device_id, feature.device_feature_id, value)
        return script

class GetCommandRange(Node):
    @staticmethod
    def get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage):
        script = """$("#widget_%s_%s").widget_mini_command_range({
                        usage: %s,
                        devicename: '%s',
                        featurename: '%s',
                        min_value: %s,
                        max_value: %s,
                        step: %s,
                        unit: '%s',
                        action: function(self, values) {
                            $.getREST(['command', '%s', '%s', '%s', values.value],
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
                    });
                    """ % (feature.device_id, feature.device_feature_id, feature.device.device_usage_id,
                           feature.device.name, feature.device_feature.name,
                           parameters_type['valueMin'], parameters_type['valueMax'],
                           parameters_usage['range']['step'], parameters_usage['range']['unit'],
                           device_type.device_technology_id, feature.device.address,
                           parameters_type['command'], feature.device_feature.return_confirmation)
        return script

    @staticmethod
    def get_setValue(feature, value):
        script = """$("#widget_%s_%s").widget_mini_command_range('setValue', %s);
                    """ % (feature.device_id, feature.device_feature_id, value)
        return script

class GetCommandTrigger():
    @staticmethod
    def get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage):
        script = """$('#widget_%s_%s').widget_mini_command_trigger({
                        usage: %s,
                        devicename: '%s',
                        featurename: '%s',
                        action: function(self) {
                            $.getREST(['command', '%s', '%s', '%s'],
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
                    });
                    """ % (feature.device_id, feature.device_feature_id, feature.device.device_usage_id,
                           feature.device.name, feature.device_feature.name,
                           device_type.device_technology_id, feature.device.address,
                           parameters_type['command'], feature.device_feature.return_confirmation)
        return script

class GetInfoBoolean():
    @staticmethod
    def get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage):
        script = """$("#widget_%s_%s").%s().%s('widget',{
                            usage: %s,
                            devicename: '%s',
                            featurename: '%s',
                            deviceid: %s,
                            key: '%s'
                        });
                 """ % (feature.device_id, feature.device_feature_id, feature.widget_id,
                        feature.widget_id, feature.device.device_usage_id,
                        feature.device.name, feature.device_feature.name,
                        feature.device_id, feature.device_feature.stat_key)
        return script

    @staticmethod
    def get_setValue(feature, value):
        script = """$("#widget_%s_%s").%s('setValue', %s);
                 """ % (feature.device_id, feature.device_feature_id,
                        feature.widget_id, value)

        return script
    
class GetInfoNumber():
    @staticmethod
    def get_widget(feature, device_type, device_usage, parameters_type, parameters_usage):
        script = """$("#widget_%s_%s").%s().%s('widget',{
                            usage: %s,
                            devicename: '%s',
                            featurename: '%s',
                            unit: '%s',
                            deviceid: %s,
                            key: '%s'
                        });
                 """ % (feature.device_id, feature.device_feature_id, feature.widget_id,
                        feature.widget_id, feature.device.device_usage_id,
                        feature.device.name, feature.device_feature.name,
                        parameters_type['unit'], feature.device_id, feature.device_feature.stat_key)
        return script

    @staticmethod
    def get_setValue(feature, value):
        script = """$("#widget_%s_%s").%s('setValue', %s);
                 """ % (feature.device_id, feature.device_feature_id,
                        feature.widget_id, value)

        return script

class GetInfoString():
    @staticmethod
    def get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage):
        script = ""
        return script

    @staticmethod
    def get_setValue(feature, value):
        script = ""
        return script

    
class GetWidget(Node):
    def __init__(self, feature):
        self.feature = template.Variable(feature)

    def render(self, context):
        feature = self.feature.resolve(context)

        device_type = DeviceTypes.get_dict_item(feature.device.device_type_id)
        device_usage = DeviceUsages.get_dict_item(feature.device.device_usage_id)

        parameters_type = None;
        if feature.device_feature.parameters != 'None':
            parameters_type = simplejson.loads(unescape(feature.device_feature.parameters))
        parameters_usage = None;
        if device_usage.default_options != 'None':
            parameters_usage = simplejson.loads(unescape(device_usage.default_options))
        
        if feature.device_feature.feature_type == "actuator":
            if feature.device_feature.value_type == "binary":
                script = GetCommandBinary.get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage)
            if feature.device_feature.value_type == "range":
                script = GetCommandRange.get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage)
            if feature.device_feature.value_type == "trigger":
                script = GetCommandTrigger.get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage)
        else : # 'Sensor'
            if feature.device_feature.value_type == "boolean":
                script = GetInfoBoolean.get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage)
            if feature.device_feature.value_type == "number":
                script = GetInfoNumber.get_widget(feature, device_type, device_usage, parameters_type, parameters_usage)
            if feature.device_feature.value_type == "string":
                script = GetInfoString.get_widget_mini(feature, device_type, device_usage, parameters_type, parameters_usage)
        return script

class GetWidgetInit(Node):
    def __init__(self, feature):
        self.feature = template.Variable(feature)

    def render(self, context):
        feature = self.feature.resolve(context)
        stat = Stats.get_latest(feature.device_id, feature.device_feature.stat_key)
        script = ""
        if len(stat.stats) > 0 :
            if feature.device_feature.feature_type == "actuator":
                if feature.device_feature.value_type == "binary":
                    script = GetCommandBinary.get_setValue(feature, "'" + stat.stats[0].value + "'")
                if feature.device_feature.value_type == "range":
                    script = GetCommandRange.get_setValue(feature, "'" + stat.stats[0].value + "'")
            else: # 'Sensor'
                if feature.device_feature.value_type == "boolean":
                    script = GetInfoBoolean.get_setValue(feature, "'" + stat.stats[0].value + "'")
                if feature.device_feature.value_type == "number":
                    script = GetInfoNumber.get_setValue(feature, "'" + stat.stats[0].value + "'")
                if feature.device_feature.value_type == "string":
                    script = GetInfoString.get_setValue(feature, "'" + stat.stats[0].value + "'")
        return script

class GetWidgetUpdate(Node):
    def __init__(self, feature, value):
        self.feature = template.Variable(feature)
        self.value = template.Variable(value)

    def render(self, context):
        feature = self.feature.resolve(context)
        value = self.value.resolve(context)
        script = ""
        if feature.device_feature.feature_type == "actuator":
            if feature.device_feature.value_type == "binary":
                script = GetCommandBinary.get_setValue(feature, value)
            if feature.device_feature.value_type == "range":
                script = GetCommandRange.get_setValue(feature, value)
        else: # 'Sensor'
            if feature.device_feature.value_type == "boolean":
                script = GetInfoBoolean.get_setValue(feature, value)
            if feature.device_feature.value_type == "number":
                script = GetInfoNumber.get_setValue(feature, value)
            if feature.device_feature.value_type == "string":
                script = GetInfoString.get_setValue(feature, value)
        return script
    
def do_get_widget(parser, token):
    """
    This returns the jquery function for creating a widget.

    Usage::

        {% get_widget feature %}
    """
    args = token.contents.split()
    if len(args) != 2:
        raise TemplateSyntaxError, "'get_widget' requires 'feature' argument"
    return GetWidget(args[1])

register.tag('get_widget', do_get_widget)
        
def do_get_widget_init(parser, token):
    """
    This returns the jquery function to init a widget.

    Usage::

        {% get_widget_init feature %}
    """
    args = token.contents.split()
    if len(args) != 2:
        raise TemplateSyntaxError, "'get_widget_init' requires 'feature' argument"
    return GetWidgetInit(args[1])

register.tag('get_widget_init', do_get_widget_init)

def do_get_widget_update(parser, token):
    """
    This returns the jquery function to update a widget.

    Usage::

        {% get_widget_update feature js_var %}
    """
    args = token.contents.split()
    if len(args) != 3:
        raise TemplateSyntaxError, "'get_widget_update' requires 'feature' argument and the js var name for value"
    return GetWidgetUpdate(args[1], args[2])

register.tag('get_widget_update', do_get_widget_update)