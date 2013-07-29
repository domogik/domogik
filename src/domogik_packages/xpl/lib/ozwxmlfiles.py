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
import sys


class OZwaveConfigException(OZwaveException):
    """"Zwave Manager exception  class"""
            
    def __init__(self, value):
        OZwaveException.__init__(self, value)
        self.msg = "OZwave XML files exception:"

class DeviceProduct():
    """Read and handle individual product file recognized by open-zwave."""
    
    def __init__(self,  path,  config):
        """Read XML file "product".xml of open-zwave C++ lib"""
        self.xml_file = path + '/'  + config
        self.xml_content = minidom.parse(self.xml_file)
        self.commandsClass = []
        for c in self.xml_content.getElementsByTagName("CommandClass") :
            cmdClass = {'id' : int(c.attributes.get("id").value.strip())}
            if cmdClass['id'] == 133 :  #<!-- Association Groups -->
                Associations = []
                try:
                    for a in c.getElementsByTagName("Associations") :
                        groups = []
                        try :
                            for g in a.getElementsByTagName("Group") :
                                group = {"index" : int(g.attributes.get("index").value.strip()),
                                              "max_associations" :  g.attributes.get("max_associations").value.strip(),
                                              "label" : g.attributes.get("label").value.strip(),
                                              "auto" : g.attributes.get("auto").value.strip()}
                                groups.append(dict(group))
                        except: pass
                        Associations.append(groups)
                except: pass
                cmdClass['associations'] = Associations
            elif cmdClass['id'] == 132 :  #<!-- COMMAND_CLASS_WAKE_UP -->
                cmdClass['create_vars'] = c.attributes.get("create_vars").value.strip()
#                print "COMMAND_CLASS_WAKE_UP"
            else :
                values = []
                try:
#                    print cmdClass
                    for v in c.getElementsByTagName("Value") :
#                        print "+++++++",  v.toxml()
                        value = {"type" :  v.attributes.get("type").value.strip(),
                                       "genre" : v.attributes.get("genre").value.strip(),
                                       "index" : int(v.attributes.get("index").value.strip()), 
                                       "value" :v.attributes.get("value").value.strip()}
                        try:
                            value["instance"] = int(v.attributes.get("instance").value.strip())
                        except: pass
                        try:
                            value["size"] = int(v.attributes.get("size").value.strip())
                        except: pass 
                        try:
                            value["units"] = v.attributes.get("units").value.strip()
                        except: pass
                        try:
                            value["min"] = int(v.attributes.get("min").value.strip()), 
                            value["max"] = int(v.attributes.get("max").value.strip()), 
                        except: pass
                        try:
                            value["help"] = v.getElementsByTagName("Help")[0].firstChild.data
                        except: pass
                        if value['type'] == 'list' :
                            items = {}
                            for i in v.getElementsByTagName("Item") :
                                items.update({int(i.attributes.get("value").value.strip()) : i.attributes.get("label").value.strip()})
                            value['items'] = items
                        values.append(dict(value))
                except: pass
#                print "********", values
                cmdClass['values'] = values
#            print cmdClass
            self.commandsClass.append(cmdClass)
        
    def getAllTranslateText(self, tabtext = []):
        """Return tab with all text should be translate"""
        for cmdC in self.commandsClass :
            for item in cmdC :
                if type(cmdC[item]) == list :
                    for i in cmdC[item] :
                        if type(i) == dict :
                            for t in i :
                                if type(i[t]) in [unicode,  str]:
                                    try :
                                        int(i[t])
                                    except :
                                        if i[t] not in tabtext :
                                            tabtext.append(i[t])
        return tabtext


class Manufacturers():
    """Read and handle list of manufacturers and products recognized by open-zwave."""
    
    def __init__(self,  path):
        """Read XML file manufacturer_specific.xml of open-zwave C++ lib"""
        self.path = path
        self.xml_file = "manufacturer_specific.xml"
        self.xml_content = minidom.parse(path + "/" + self.xml_file)
        # read xml file
        self.manufacturers = [];
        self.xmlns = self.xml_content.getElementsByTagName("ManufacturerSpecificData")[0].attributes.get("xmlns").value.strip()
#        print self.xmlns
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
                    except: pass
                    products.append(product)
           #         print "  -",  product
            except: pass
            if products != [] :
                item["products"] = products
            self.manufacturers.append(item)
     #  print self.manufacturers 
    
    def getMemoryUsage(self):
        """Renvoi l'utilisation memoire en octets"""
        return sys.getsizeof(self) + sum(sys.getsizeof(v) for v in self.__dict__.values()) + sys.getsizeof(self.xml_content)

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
            except: pass
            if mf : retval.append(mf)
        return retval
        
    def getProduct(self,  name) :
        """Return all informations of a product."""
        products = self.searchProduct(name)
        if products[0] : 
#            print products[0]['products'][0]
            if products[0]['products'][0].has_key('config') :
                return DeviceProduct(self.path, products[0]['products'][0]['config'])
            else : return None
        else :
            return None
            
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
            except: pass
            if mf : retval.append(mf)
        return retval
    
    def getAllProductsName(self):
        """Retourn all products recognized without doublon."""
        manufacturers = []
        for m in self.manufacturers:
            products=[]
            try:
                for p in m['products']:
                    newP = True
                    if p.has_key('config') : conf = p['config']
                    else : conf =""
                    for rP in products :
                        if p['name'] == rP['name'] and conf == rP['config'] :
                   #     i = products.index(p['name']).index(p['id'])
                            rP['ids'].append(p['id'])
                            newP = False
                    if newP :
                  # if i = p['name'] not in products :
                        prod = {'name': p['name'], 'type': p['type'], 'ids': [p['id']]}
                        prod .update({'config': conf})
                        products.append(prod)
            except: pass
            manufacturers.append({'manufacturer': m['name'], 'id': m['id'],  'products': products})
        return manufacturers
    
    def getAllProductsTranslateText(self):
        tabtext=[]
        products=[]
        productsName=[]
        for m in self.manufacturers:
            try:
                for p in m['products'] :
                    if p['name'] not in productsName :
                        productsName.append(p['name'])
                        products.append(p)
                    if p.has_key('config') :
                        prod = DeviceProduct(self.path, p['config'])
                        if prod : prod.getAllTranslateText(tabtext)
            except: pass
        return {'products':products, 'tabtext' : tabtext}

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
            try :
                item['name'] = n.attributes.get("name").value.strip()
                item['max_baud_rate'] = int(n.attributes.get("max_baud_rate").value.strip())
            except : pass
            try :
                m = n.getElementsByTagName('Manufacturer')[0]
            except : pass
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
                    except: pass
                    cmdsClass.append(cmdClass)
            except: pass
            if cmdsClass != [] :
                item["cmdsClass"] = cmdsClass
            self.nodes.append(item)
        print self.nodes 



if __name__ == "__main__":
    listManufacturers = Manufacturers("/home/admdomo/python-openzwave/openzwave/config")
#    listManufacturers = Manufacturers("D:\Python_prog\open-zwave\config")
    print listManufacturers.getManufacturer('0x86')
    print listManufacturers.searchProduct('Thermostat')
    print '*************** searchProductType'
    print listManufacturers.searchProductType('0x0400',  '0x0106')
    tabtext = listManufacturers.getProduct('FGS211 Switch 3kW').getAllTranslateText()
 #   listNodes = networkFileConfig('/home/admdomo/domogik/src/share/domogik/data/ozwave/zwcfg_0x014d0f18.xml')
    toTranslate = listManufacturers.getAllProductsTranslateText()
    fich = open("/var/tmp/exporttrad.txt", "w")
#    fich = open("D:/Python_prog/test/exporttrad.txt", "w")
#    for prod in  toTranslate['products']:
#        print prod
#        fich.write(prod['name'].encode('utf8').replace('\n','\r') + '\n\n')
    for ligne in toTranslate['tabtext']:
        fich.write(ligne.encode('utf8').replace('\n','\r') + '\n\n')
    fich.close()
    
