#!/usr/bin/python 
# -*- coding:utf-8 -*-

from xml.dom import minidom
import glob
import os.path

from domogik.xpl.lib.module import *
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader

class TestXml:
    def parse(self,url):
        cfg = Loader('domogik')
        config = cfg.load()
        db = dict(config[1])
        #directory = "%s/xml/rest/" % db['cfg_path']
        directory = "/home/maxence/"
#        files = glob.glob("%s/*xml" % directory)
        if url[0] == '/':
            url = url[1:]

        cmd, techno, address, order  = self.split_url(url, directory)
        file = "%s/%s.xml" % (directory, techno)
        doc = minidom.parse(file)
        
        
        mapping = doc.documentElement
        if mapping.getElementsByTagName("technology")[0].attributes.get("name").value != techno:
            raise ValueError, "'technology' attribute must be the same as file name !"

        #Schema
        schema = mapping.getElementsByTagName("schema")[0].firstChild.nodeValue

        #Device key name
        device = mapping.getElementsByTagName("device")[0]
        if device.getElementsByTagName("key") != []:
            device_address_key = device.getElementsByTagName("key")[0].firstChild.nodeValue
        else:
            device_address_key = None

        #Orders
        orders = mapping.getElementsByTagName("orders")[0]
        order_key = orders.getElementsByTagName("key")[0].firstChild.nodeValue

        #Get the good order bloc :
        the_order = None
        for an_order in orders.getElementsByTagName("order"):
            if an_order.getElementsByTagName("name")[0].firstChild.nodeValue == order:
                the_order = an_order
        if the_order == None:
            raise ValueError, "Order can't be found"

        #Parse the order bloc
        order_value = the_order.getElementsByTagName("value")[0].firstChild.nodeValue
        #mandatory parameters
        mandatory_parameters_value = {}
        optional_parameters_value = {}
        if the_order.getElementsByTagName("parameters")[0].hasChildNodes():
            mandatory_parameters = the_order.getElementsByTagName("parameters")[0].getElementsByTagName("mandatory")[0]
            count_mandatory_parameters = len(mandatory_parameters.getElementsByTagName("parameter"))
            mandatory_parameters_from_url = url.split('/')[4:4+count_mandatory_parameters]
            for mandatory_param in mandatory_parameters.getElementsByTagName("parameter"):
                key = mandatory_param.attributes.get("key").value
                value = mandatory_parameters_from_url[int(mandatory_param.attributes.get("location").value) - 1]
                mandatory_parameters_value[key] = value
            #optional parameters 
            if the_order.getElementsByTagName("parameters")[0].getElementsByTagName("optional") != []:
                optional_parameters =  the_order.getElementsByTagName("parameters")[0].getElementsByTagName("optional")[0]
                for opt_param in optional_parameters.getElementsByTagName("parameter"):
                    ind = url.index(opt_param.getElementsByTagName("name")[0])
                    optional_parameters_value[url[ind]] = url[ind + 1]
        
        return self._forge_msg(schema, device_address_key, address, order_key, order_value, mandatory_parameters_value, optional_parameters_value)

    def _forge_msg(self, schema, device_address_key, address, order_key, order_value, mandatory_parameters_value, optional_parameters_value):
        msg = """xpl-cmnd
{
hop=1
source=CHANGE-THAT
target=*
}
%s
{
%s=%s
%s=%s
""" % (schema, device_address_key, address, order_key, order_value)
        for m_param in mandatory_parameters_value.keys():
            msg += "%s=%s\n" % (m_param, mandatory_parameters_value[m_param])
        for o_param in optional_parameters_value.keys():
            msg += "%s=%s\n" % (o_param, optional_parameters_value[o_param])
        msg += "}"
        return msg




    def split_url(self, url, directory):
        """ Split an url, check it is correct, and  return the parsed attributes : 
        @return : command, technology, address, [mandatory_params], {optionnal:params}
        """
        if url[0] == '/':
            url = url[1:]
        fields = url.split('/')
        command = fields[0]
        if command != 'command':
            raise AttributeError, "This module must not be used for anything else than 'command' requests"
        technology = fields[1]
        if not os.path.isfile('%s/%s.xml' % (directory, technology) ):
            raise ValueError, "This technology is not known (no xml file with its name)"
        address = fields[2]
        order = fields[3]
        return command, technology, address, order

if __name__ == "__main__":
    test = TestXml()
    print test.parse("/command/x10/a3/on")
    print test.parse("/command/x10/a3/dim/10")
