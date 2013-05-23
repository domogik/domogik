# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}$

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

Plugin purpose
==============

Support Z-wave technology

Implements
==========

Read openzwave lib C++ xml files configurations

@author: Nico <nico84dev@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from ozwdefs import *
import libopenzwave
from libopenzwave import PyManager
from xml.dom import minidom
import json


class OZwaveConfigException(OZwaveException):
    """"Zwave Manager exception  class"""
            
    def __init__(self, value):
        OZwaveException.__init__(self, value)
        self.msg = "OZwave XML files exception:"

class Manufacturers():
    """Read and handle list of manufacturers and products recognized by open-zwave"""
    
    def __init__(self,  path):
        """Read XML file manufacturer_specific.xml of open-zwave C++ lib"""
        self.xml_file = path + "/manufacturer_specific.xml"
        self.xml_content = minidom.parse(self.xml_file)
        # read xml file
        self.manufacturers = [];
        self.xmlns = self.xml_content.getElementsByTagName("ManufacturerSpecificData")[0].attributes.get("xmlns").value.strip()
        print self.xmlns
        for m in self.xml_content.getElementsByTagName("Manufacturer"):
            item = {'id' : hex(int(m.attributes.get("id").value.strip(), 16)),  'name' : m.attributes.get("name").value.strip()}
            products = []
            try:
                for p in m.getElementsByTagName("Product"):
                    product = {"type" :  hex(int(p.attributes.get("type").value.strip(), 16)), 
                                       "id" : hex(int(p.attributes.get("id").value.strip(), 16)), 
                                       "name" :p.attributes.get("name").value.strip()}
                    try:
                        product["config"] = p.attributes.get("config").value.strip()
                    except:
                        pass
                    products.append(product)
           #         print "  -",  product
            except:
                pass
            if products != [] :
                item["products"] = products
            self.manufacturers.append(item)
     #  print self.manufacturers 
        
    def getManufacturer(self, manufacturer):
        """Return Manufacturer and products if is recognized by name or id."""
        retval = None
        try :
            int(manufacturer,  16)
            ref= 'id'
        except:
            ref = 'name'
        for m in self.manufacturers :
            if m[ref] == manufacturer : 
                retval = m
                break
        return retval
    
    def searchProduct(self,  product):
        """Return Product and Manufacturer if product is find."""
        retval = []
        for m in self.manufacturers:
            mf = None
            try:
                for p in m['products']:
                    if product in p['name'] :
                        if not mf : mf = {'id': m['id'],  'name': m['name'],  'products': []}
                        mf['products'].append(p)
            except:
                pass
            if mf : retval.append(mf)
        return retval
        
    def searchProductType(self,  type,  id = None):
        """Return Product and Manufacturer if product is find."""
        retval = []
        type = int(type, 16)
        if id : id = int(id, 16)
        for m in self.manufacturers:
            mf = None
            try:
                for p in m['products']:
                    if type == int(p['type'], 16) and (not id or (id == int(p['id'],  16))) :
                        if not mf : mf = {'id': m['id'],  'name': m['name'],  'products': []}
                        mf['products'].append(p)
            except:
                pass
            if mf : retval.append(mf)
        return retval
        
class networkFileConfig():
    """Read and manage open-zwave xml zwave Network composing"""
    
    def __init__(self,  path):
        """Read XML file zwcfg_<HOMEID>.xml of open-zwave C++ lib"""
        self.xml_file = path
        self.xml_content = minidom.parse(self.xml_file)
        # read xml file
        self.nodes = [];
        self.version = self.xml_content.getElementsByTagName("Driver")[0].attributes.get("version").value.strip()
        print 'Driver version : %s' % self.version
        for n in self.xml_content.getElementsByTagName("Node"):         
            item = {'id' : int(n.attributes.get("id").value.strip())}
            print n ,  item['id']
            item['name'] = n.attributes.get("name").value.strip()
            item['max_baud_rate'] = int(n.attributes.get("id").value.strip())
            m = n.getElementsByTagName('Manufacturer')[0]
            print m
            item['manufacturer'] = {'id' : m.attributes.get("id").value.strip(), 
                                                    'name' : m.attributes.get("name").value.strip(), }
            item['product'] = {'type' :m.getElementsByTagName('Product')[0].attributes.get("type").value.strip(), 
                                            'id' : m.getElementsByTagName('Product')[0].attributes.get("id").value.strip(), 
                                            'name' :m.getElementsByTagName('Product')[0].attributes.get("name").value.strip(), }
            cmdsClass = []
            try:
                for c in m.getElementsByTagName("CommandClass"):
                    cmdClass = {"version" :  hex(int(c.attributes.get("version").value.strip(), 16)), 
                                       "id" : hex(int(c.attributes.get("id").value.strip(), 16)), 
                                       "name" :c.attributes.get("name").value.strip()}
                    try:
                        cmdClass["config"] = c.attributes.get("config").value.strip()
                    except:
                        pass
                    cmdsClass.append(cmdClass)
            except:
                pass
            if cmdsClass != [] :
                item["cmdsClass"] = cmdsClass
            self.nodes.append(item)
        print self.nodes 


if __name__ == "__main__":
    listManufacturers = Manufacturers("/home/admdomo/python-openzwave/open-zwave/config")
    print listManufacturers.getManufacturer('0x86')
    print listManufacturers.searchProduct('Thermostat')
    print '*************** searchProductType'
    print listManufacturers.searchProductType('0x0400',  '0x0106')
    listNodes = networkFileConfig('/home/admdomo/domogik/src/share/domogik/data/ozwave/zwcfg_0x014d0f18.xml')
    
            
            
        
