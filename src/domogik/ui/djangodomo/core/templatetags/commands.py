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

class GetActuator(Node):
    @staticmethod
    def get_widget(associationid, widgetid, feature, device_type, device_usage, parameters_type, parameters_usage):
        script = """$('#widget_%s').%s({
                        usage: %s,
                        devicename: '%s',
                        featurename: '%s',
                        devicetechnology: '%s',
                        deviceaddress: '%s',
                        featureconfirmation: '%s',
                        usage_parameters: %s,
                        model_parameters: %s
                    });
                    """ % (associationid, widgetid,
                           feature.device.device_usage_id,
                           feature.device.name, feature.device_feature_model.name,
                           device_type.device_technology_id, feature.device.address,
                           feature.device_feature_model.return_confirmation,
                           simplejson.dumps(parameters_usage['actuator'][feature.device_feature_model.value_type]),
                           simplejson.dumps(parameters_type))
        return script

    @staticmethod
    def get_setValue(associationid, widgetid, feature, value):
        script = """$("#widget_%s").%s('setValue', %s);
                    """ % (associationid, widgetid, value)
        return script

class GetSensor():
    @staticmethod
    def get_widget(associationid, widgetid, feature, device_type, device_usage, parameters_type, parameters_usage):
        script = """$("#widget_%s").%s({
                            usage: %s,
                            devicename: '%s',
                            featurename: '%s',
                            deviceid: %s,
                            key: '%s',
                            usage_parameters: %s,
                            model_parameters: %s
                        });
                 """ % (associationid, widgetid,
                        feature.device.device_usage_id,
                        feature.device.name, feature.device_feature_model.name,
                        feature.device_id, feature.device_feature_model.stat_key,
                        simplejson.dumps(parameters_usage['sensor'][feature.device_feature_model.value_type]),
                        simplejson.dumps(parameters_type))
        return script

    @staticmethod
    def get_setValue(associationid, widgetid, feature, value):
        script = """$("#widget_%s").%s('setValue', %s);
                 """ % (associationid, widgetid, value)

        return script
    
class GetWidget(Node):
    def __init__(self, associationid, widgetid, feature):
        self.associationid = template.Variable(associationid)
        self.widgetid = template.Variable(widgetid)
        self.feature = template.Variable(feature)

    def render(self, context):
        associationid = self.associationid.resolve(context)
        widgetid = self.widgetid.resolve(context)
        feature = self.feature.resolve(context)

        device_type = DeviceTypes.get_dict_item(feature.device.device_type_id)
        device_usage = DeviceUsages.get_dict_item(feature.device.device_usage_id)

        parameters_type = None;
        if feature.device_feature_model.parameters != 'None':
            parameters_type = simplejson.loads(unescape(feature.device_feature_model.parameters))
        parameters_usage = None;
        if device_usage.default_options != 'None':
            parameters_usage = simplejson.loads(unescape(device_usage.default_options))
        
        if feature.device_feature_model.feature_type == "actuator":
            script = GetActuator.get_widget(associationid, widgetid, feature, device_type, device_usage, parameters_type, parameters_usage)            
        else : # 'Sensor'
            script = GetSensor.get_widget(associationid, widgetid, feature, device_type, device_usage, parameters_type, parameters_usage)
        return script

class GetWidgetInit(Node):
    def __init__(self, associationid, widgetid, feature):
        self.associationid = template.Variable(associationid)
        self.widgetid = template.Variable(widgetid)
        self.feature = template.Variable(feature)

    def render(self, context):
        associationid = self.associationid.resolve(context)
        widgetid = self.widgetid.resolve(context)
        feature = self.feature.resolve(context)
        stat = Stats.get_latest(feature.device_id, feature.device_feature_model.stat_key)
        script = ""
        if len(stat.stats) > 0 :
            if feature.device_feature_model.feature_type == "actuator":
                script = GetActuator.get_setValue(associationid, widgetid, feature, "'" + stat.stats[0].value + "'")
            else: # 'Sensor'
                script = GetSensor.get_setValue(associationid, widgetid, feature, "'" + stat.stats[0].value + "'")
        return script

class GetWidgetUpdate(Node):
    def __init__(self, associationid, widgetid, feature, value):
        self.associationid = template.Variable(associationid)
        self.widgetid = template.Variable(widgetid)
        self.feature = template.Variable(feature)
        self.value = template.Variable(value)

    def render(self, context):
        associationid = self.associationid.resolve(context)
        widgetid = self.widgetid.resolve(context)
        feature = self.feature.resolve(context)
        value = self.value.resolve(context)
        script = ""
        if feature.device_feature_model.feature_type == "actuator":
            script = GetActuator.get_setValue(associationid, widgetid, feature, value)
        else: # 'Sensor'
            script = GetSensor.get_setValue(associationid, widgetid, feature, value)
        return script
    
def do_get_widget(parser, token):
    """
    This returns the jquery function for creating a widget.

    Usage::

        {% get_widget associationid widgetid feature %}
    """
    args = token.contents.split()
    if len(args) != 4:
        raise TemplateSyntaxError, "'get_widget' requires arguments"
    return GetWidget(args[1], args[2], args[3])

register.tag('get_widget', do_get_widget)
        
def do_get_widget_init(parser, token):
    """
    This returns the jquery function to init a widget.

    Usage::

        {% get_widget_init associationid widgetid feature %}
    """
    args = token.contents.split()
    if len(args) != 4:
        raise TemplateSyntaxError, "'get_widget_init' requires arguments"
    return GetWidgetInit(args[1], args[2], args[3])

register.tag('get_widget_init', do_get_widget_init)

def do_get_widget_update(parser, token):
    """
    This returns the jquery function to update a widget.

    Usage::

        {% get_widget_update associationid widgetid feature js_var %}
    """
    args = token.contents.split()
    if len(args) != 5:
        raise TemplateSyntaxError, "'get_widget_update' requires arguments and the js var name for value"
    return GetWidgetUpdate(args[1], args[2], args[3], args[4])

register.tag('get_widget_update', do_get_widget_update)