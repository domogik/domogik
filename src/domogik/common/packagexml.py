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

Plugin purpose
==============

Library to simply manager plugin's xml file description

Implements
==========

PackageXml

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.configloader import Loader
from xml.dom import minidom
import traceback
import urllib2
import datetime
import json




class PackageException(Exception):
    """
    Package exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class PackageXml():
    """ Package Xml class
        Used to represent a package xml as a python object
    """
    def __init__(self, id = None, url = None, path = None, pkg_type = "plugin"):
        """ Read xml file of a plugin and make an object from it
            @param id : name of package
            @param url : url of xml file
            @param path : path of xml file
            @param pkg_type : package type (default : 'plugin')
                          To use only with id != None
        """
        xml_file = None
        try:
            # load xml from repository
            if id != None:
                # get config
                cfg = Loader('domogik')
                config = cfg.load()
                conf = dict(config[1])

                if pkg_type == "plugin":
                    if conf.has_key('package_path'):
                        xml_directory = "%s/domogik_packages/plugins/" % (conf['package_path'])
                    else:
                        xml_directory = "%s/%s" % (conf['src_prefix'], "share/domogik/plugins/")
                elif pkg_type == "external":
                    if conf.has_key('package_path'):
                        xml_directory = "%s/domogik_packages/externals/" % (conf['package_path'])
                    else:
                        xml_directory = "%s/%s" % (conf['src_prefix'], "share/domogik/externals/")
                else:
                    raise PackageException("Type '%s' doesn't exists" % pkg_type)
                xml_file = "%s/%s.xml" % (xml_directory, id)

                self.info_file = xml_file
                self.xml_content = minidom.parse(xml_file)

                # icon file
                if conf.has_key('package_path'):
                    xml_directory = "%s/domogik_packages/design/" % (conf['package_path'])
                else:
                    self.icon_file = "%s/%s/%s/%s/icon.png" % (conf['src_prefix'], "share/domogik/design/", pkg_type, id)
    
            elif path != None:
                xml_file = path
                self.info_file = xml_file
                self.xml_content = minidom.parse(xml_file)
                self.icon_file = None

            elif url != None:
                xml_file = url
                self.info_file = xml_file
                xml_data = urllib2.urlopen(xml_file)
                self.xml_content = minidom.parseString(xml_data.read())
                self.icon_file = None

            # read xml file
            self.type = self.xml_content.getElementsByTagName("package")[0].attributes.get("type").value.strip()
            self.id = self.xml_content.getElementsByTagName("id")[0].firstChild.nodeValue.strip()
            self.desc = self.xml_content.getElementsByTagName("description")[0].firstChild.nodeValue.strip()
            self.changelog = self.xml_content.getElementsByTagName("changelog")[0].firstChild.nodeValue.strip()
            self.release = self.xml_content.getElementsByTagName("version")[0].firstChild.nodeValue.strip()
            try:
                self.generated = self.xml_content.getElementsByTagName("generated")[0].firstChild.nodeValue.strip()
            except:
                self.generated = "n/a"
            self.doc = self.xml_content.getElementsByTagName("documentation")[0].firstChild.nodeValue.strip()
            self.author = self.xml_content.getElementsByTagName("author")[0].firstChild.nodeValue.strip()
            self.email = self.xml_content.getElementsByTagName("author-email")[0].firstChild.nodeValue.strip()
            try:
                self.domogik_min_release = self.xml_content.getElementsByTagName("domogik-min-version")[0].firstChild.nodeValue.strip()
            except:
                # if no restriction, compatible since 0.1.0 (first release)
                self.domogik_min_release = "0.1.0"

            # external specific
            if self.type == "external":
                self.vendor_id = self.xml_content.getElementsByTagName("vendor-id")[0].firstChild.nodeValue.strip()
                self.device_id = self.xml_content.getElementsByTagName("device-id")[0].firstChild.nodeValue.strip()
            else:
                self.vendor_id = None
                self.device_id = None


            # list of configurations keys
            self.configuration = []
            config = self.xml_content.getElementsByTagName("configuration-keys")[0]
            for key in config.getElementsByTagName("key"):
                try:
                    k_interface = key.getElementsByTagName("interface")[0].firstChild.nodeValue
                except IndexError:
                    # no value in interface
                    k_interface = "no"
                try:
                    k_optionnal = key.getElementsByTagName("optionnal")[0].firstChild.nodeValue
                except IndexError:
                    # Optionnal value
                    k_optionnal = "no"
                k_id = key.getElementsByTagName("order-id")[0].firstChild.nodeValue
                k_key = key.getElementsByTagName("name")[0].firstChild.nodeValue
                k_desc = key.getElementsByTagName("description")[0].firstChild.nodeValue
                k_type = key.getElementsByTagName("type")[0].firstChild.nodeValue
                k_options = []
                if k_type == "enum":
                    try:
                        options = key.getElementsByTagName("options")[0]
                        for option in options.getElementsByTagName("option"):
                            k_options.append( option.firstChild.nodeValue )
                    except IndexError:
                        k_options = []
                try:
                    k_default = key.getElementsByTagName("default-value")[0].firstChild.nodeValue
                except AttributeError:
                    # no value in default
                    k_default = None
                self.configuration.append({"id" : k_id,
                                           "interface" : k_interface,
                                           "optionnal" : k_optionnal,
                                           "key" : k_key,
                                           "description" : k_desc,
                                           "type" : k_type,
                                           "options": k_options,
                                           "default" : k_default})

            # list of files
            self.files = []
            xml_data = self.xml_content.getElementsByTagName("files")[0]
            for my_file in xml_data.getElementsByTagName("file"):
                data = {"path" :  my_file.attributes.get("path").value.strip()}
                self.files.append(data)

            # list of external files
            self.external_files = []
            try:
                xml_data = self.xml_content.getElementsByTagName("external_files")[0]
                for my_file in xml_data.getElementsByTagName("file"):
                    data = {"path" :  my_file.attributes.get("path").value.strip()}
                    self.external_files.append(data)
            except:
                pass

            # all files
            self.all_files = list(self.files)
            self.all_files.extend(self.external_files)

            # list of dependencies
            self.dependencies = []
            xml_data = self.xml_content.getElementsByTagName("dependencies")[0]
            for dep in xml_data.getElementsByTagName("dep"):
                dep_type = dep.attributes.get("type").value.strip()
                dep_id = dep.attributes.get("id").value.strip()
                data = {"type" : dep_type,
                        "id" : dep_id}
                self.dependencies.append(data)

            # list of udev rules
            self.udev_rules = []
            xml_data = self.xml_content.getElementsByTagName("udev-rules")[0]
            for dep in xml_data.getElementsByTagName("rule"):
                rule_model = dep.attributes.get("model").value.strip()
                rule_desc = dep.attributes.get("description").value.strip()
                rule_filename = dep.attributes.get("filename").value.strip()
                rule_content = dep.firstChild.nodeValue.strip()
                data = {"model" : rule_model,
                        "desc" : rule_desc,
                        "filename" : rule_filename,
                        "rule" : rule_content}
                self.udev_rules.append(data)

            # construct filenames
            self.fullname = "%s-%s" % (self.type, self.id)
            self.xml_filename = "%s-%s-%s.xml" % (self.type, self.id, self.release)
            self.pkg_filename = "%s-%s-%s.tgz" % (self.type, self.id, self.release)

            # repository specifics
            rep = self.xml_content.getElementsByTagName("repository")
            if len(rep) == 0:
                self.package_url = None
                self.priority = None
                self.source = None
            else:
                try:
                    self.package_url = rep[0].attributes.get("package").value.strip()
                except AttributeError:
                    self.package_url = None
                try:
                    self.priority = rep[0].attributes.get("priority").value.strip()
                except AttributeError:
                    self.priority = None
                try:
                    self.source = rep[0].attributes.get("source").value.strip()
                except AttributeError:
                    self.source = None

            # data for database
            dtec = self.xml_content.getElementsByTagName("device_technology")[0]
            self.technology = {}
            self.technology["id"] = dtec.getElementsByTagName("id")[0].firstChild.nodeValue.strip()
            self.techno = self.technology["id"]
            self.technology["name"] = dtec.getElementsByTagName("name")[0].firstChild.nodeValue.strip()
            self.technology["description"] = dtec.getElementsByTagName("description")[0].firstChild.nodeValue.strip()
            
            dtypes = self.xml_content.getElementsByTagName("device_types")[0]
            self.device_types = []
            for dtype in dtypes.getElementsByTagName("device_type"):
                self.device_types.append({
                        "id" : dtype.getElementsByTagName("id")[0].firstChild.nodeValue.strip(),
                        "name" : dtype.getElementsByTagName("name")[0].firstChild.nodeValue.strip(),
                        "description" : dtype.getElementsByTagName("description")[0].firstChild.nodeValue.strip()
                        })
            
            #dusages = self.xml_content.getElementsByTagName("device_usages")[0]
            #self.device_usages = []
            #for dusage in dusages.getElementsByTagName("device_usage"):
            #    self.device_usages.append({
            #            "id" : dusage.getElementsByTagName("id")[0].firstChild.nodeValue,
            #            "name" : dusage.getElementsByTagName("name")[0].firstChild.nodeValue,
            #            "description" : dusage.getElementsByTagName("description")[0].firstChild.nodeValue,
            #            "default_options" : dusage.getElementsByTagName("default_options")[0].firstChild.nodeValue
            #            })
            
            dfms = self.xml_content.getElementsByTagName("device_feature_models")[0]
            self.device_feature_models = []
            for dfm in dfms.getElementsByTagName("device_feature_model"):
                try:
                    stat_key = dfm.getElementsByTagName("stat_key")[0].firstChild.nodeValue.strip()
                except AttributeError:
                    stat_key = ""
                self.device_feature_models.append({
                        "id" : dfm.getElementsByTagName("id")[0].firstChild.nodeValue.strip(),
                        "name" : dfm.getElementsByTagName("name")[0].firstChild.nodeValue.strip(),
                        "feature_type" : dfm.getElementsByTagName("feature_type")[0].firstChild.nodeValue.strip(),
                        "device_type_id" : dfm.getElementsByTagName("device_type_id")[0].firstChild.nodeValue.strip(),
                        "value_type" : dfm.getElementsByTagName("value_type")[0].firstChild.nodeValue.strip(),
                        "stat_key" : stat_key,
                        "parameters" : dfm.getElementsByTagName("parameters")[0].firstChild.toxml().strip(),
                        "return_confirmation" : dfm.getElementsByTagName("return_confirmation")[0].firstChild.nodeValue.strip()
                        })

        except:
            raise PackageException("Error reading xml file : %s : %s" % (xml_file, str(traceback.format_exc())))


    def cache_xml(self, cache_folder, url, repo_url, priority):
        """ Add package url info in xml data
            Store xml in a file in cache_folder
            @param cache_folder : folder to put xml file
            @param url : package url
            @param repo_url : repository url
            @param priority : repository priority
        """
        top_elt = self.xml_content.documentElement
        new_elt = self.xml_content.createElementNS(None, 'repository')
        new_elt.setAttribute("package", url)
        new_elt.setAttribute("priority", priority)
        new_elt.setAttribute("source", repo_url)
        top_elt.appendChild(new_elt)
        cache_file = open("%s/%s" % (cache_folder, self.xml_filename), "w") 
        cache_file.write(self.xml_content.toxml().encode("utf-8"))
        cache_file.close()

    def set_repo_source(self, source):
        """ Add source info in xml data
            Store in xml the repository from which it comes
            @param source : repository url
        """
        top_elt = self.xml_content.documentElement
        new_elt = self.xml_content.createElementNS(None, 'repository')
        new_elt.setAttribute("source", source)
        top_elt.appendChild(new_elt)
        my_file = open("%s" % (self.info_file), "w") 
        my_file.write(self.xml_content.toxml().encode("utf-8"))
        my_file.close()

    def set_generated(self, xml_path):
        """ Add generation date info in xml data
            @param xml_path : path to xml file
        """
        top_elt = self.xml_content.documentElement
        new_elt = self.xml_content.createElement('generated')
        text = self.xml_content.createTextNode(str(datetime.datetime.now()))
        new_elt.appendChild(text)
        top_elt.appendChild(new_elt)
        cache_file = open(xml_path, "w") 
        cache_file.write(self.xml_content.toxml().encode("utf-8"))
        cache_file.close()

    def display(self):
        """ Display xml data in a fine way
        """
        print("---- Package informations -------------------------------")
        print("Type                : %s" % self.type)
        print("Id                  : %s" % self.id)
        print("Full name           : %s" % self.fullname)
        print("Release             : %s" % self.release)
        print("Technology          : %s" % self.techno)
        if self.type == "external":
            print("xPL vendor id       : %s" % self.vendor_id)
            print("xPL device id       : %s" % self.device_id)
        print("Link for doc        : %s" % self.doc)
        print("Description         : %s" % self.desc)
        print("Changelog           : %s" % self.changelog)
        print("Author              : %s" % self.author)
        print("Author's email      : %s" % self.email)
        print("Domogik min release : %s" % self.domogik_min_release)
        print("----- Python dependencies -------------------------------")
        for dep in self.dependencies:
            print("- %s %s" % (dep["type"], dep["id"]))
        print("----- UDev rules ----------------------------------------")
        for rule in self.udev_rules:
            print("- %s (%s) in '%s'" % (rule["model"], rule["desc"], rule["filename"]))
            print("  Rule : %s" % rule["rule"])
        print("----- Package files -------------------------------------")
        for my_file in self.files:
            print("- %s" % my_file["path"])
        print("----- Package external files ----------------------------")
        for my_file in self.external_files:
            print("- %s" % my_file["path"])
        if self.package_url != None:
            print("----- Repository informations ---------------------------")
            print("Package path        : %s" % self.package_url)
            print("Priority            : %s" % self.priority)
        print("---------------------------------------------------------")

    def get_json(self):
        """ transform xml in json
        """
        my_json = \
        {
            "json_version" : 1,
            "identity" : {
                "type" : self.type,
                "id" : self.id,
                "version" : self.release,
                "name" : self.id,   
                "fullname" : self.fullname,  
                "category" : self.techno,
                "description" : self.desc,
                "documentation" : self.doc,
                "changelog" : self.changelog,
                "author" : self.author,
                "author_email" : self.email,
                "domogik_min_version" : self.domogik_min_release,
            },
        }

        # external members specific
        if self.type == "external":
            my_json["external"] = {"vendor_id" : self.vendor_id,
                                   "device_id" : self.device_id}

        # dependencies
        my_dep = []
        for dep in self.dependencies:
            my_dep.append({"type" : dep["type"],
                           "id" : dep["id"]})
        my_json["identity"]["dependencies"] = my_dep

        # udev rules
        my_udev = [] 
        for rule in self.udev_rules:
            my_udev.append({"model" : rule["model"],
                            "description" : rule["desc"],
                            "filename" : rule["filename"],
                            "rule" : rule["rule"]})
        my_json["udev-rules"] = my_udev

        # package files
        my_files = []
        for my_file in self.files:
            my_files.append(my_file["path"])
        my_json["files"] = my_files
        
        # configuration elements
        my_json["configuration"] = self.configuration

        # external files
        # ! TODO !

        # cache related informations
        if self.package_url != None:
            my_json["package-url"] = self.package_url
            my_json["priority"] = self.priority

        # technology detail
        my_json["technology"] = self.technology

        # type
        my_json["device_types"] = self.device_types 

        # features
        my_json["device_feature_models"] = self.device_feature_models 
            
        print("# Some updates needs to be done manually :")
        print("# - adapt the file path in 'files' : src/domogik/xpl/* => src/domogik_packages/xpl/*")
        print("# - rename the xml file as json in 'files' : src/share/domogik/plugins/myplugin.xml => src/..../myplugin.json")
        return json.dumps(my_json, sort_keys=True, indent=4)

if __name__ == "__main__":
    PX = PackageXml("ipx800")
    print(PX.get_json())
