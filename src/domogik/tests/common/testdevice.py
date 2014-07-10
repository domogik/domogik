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

Purpose
=======

Tools for regression tests

Usage
=====

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""



from domogik.tests.common.helpers import get_rest_url
from domogik.common.utils import get_sanitized_hostname
import requests
import json
import sys


class TestDevice():
    """ Tool to create test instances
    """

    def __init__(self):
        """ Construtor
            @param rest_url : url of the rest server
        """
        # rest url
        self.rest_url = get_rest_url()

        # package informations
        self.client_id = None

        # instance informations
        self.instance_name = None
        self.instance_type = None

    def create_instance(self, client_id, instance_name, instance_type):
        """ Call POST /instance/... to create the instance
            @param client_id : client id
            @param instance_name : the instance name
            @param instance_type : the instance type
            @return : the instance id for the instance created
        """
        # package informations
        self.client_id = client_id
        # instance informations
        self.instance_name = instance_name
        self.instance_type = instance_type
        description = "a test instance"
        reference = "for test only"
        print(u"Create a test instance for {0}. Device type is '{1}', name is '{2}'".format(self.client_id,
                                                                                                          self.instance_type,
                                                                                                          self.instance_name))

        response = requests.post("{0}/instance/".format(self.rest_url), \
            headers={'content-type':'application/x-www-form-urlencoded'},
            data="name={0}&client_id={1}&description={2}&reference={3}&instance_type={4}".format(self.instance_name,
                                                                                               self.client_id,
                                                                                               description,
                                                                                               reference,
                                                                                               self.instance_type))
        print(u"Response : [{0}]".format(response.status_code))
        #print(u"Response : [{0}] {1}".format(response.status_code, response.text))
        if response.status_code != 201:
            raise RuntimeError("Error when creating the instance : {0}".format(response.text))

        # get the instance id for later calls to REST
        instance = json.loads(response.text)
        self.instance_id = instance['id']
        print(u"The instance id is '{0}'".format(self.instance_id))
        return self.instance_id

    def configure_global_parameters(self, params):
        """ Call PUT /instance/addglobal/... to set the global parameters for a instance
            @param params : dict of params
        """
        print(u"Configure the global parameters...")
        # build the data part
        first = True
        data = ""
        for key in params:
            if first == False:
                data += "&"
            else:
                first = False
            data += "{0}={1}".format(key, params[key])
        response = requests.put("{0}/instance/addglobal/{1}".format(self.rest_url, self.instance_id), \
                                 headers={'content-type':'application/x-www-form-urlencoded'},
                                 data="{0}".format(data))
        print(u"Response : [{0}]".format(response.status_code))
        #print(u"Response : [{0}] {1}".format(response.status_code, response.text))
        if response.status_code != 200:
            raise RuntimeError("Error when configuring the instance global parameters : {0}".format(response.text))

    def del_instance(self, id):
        """ Call DELETE /instance/... to delete a instance
            @param id : instance id
        """
        print(u"Delete the instance : id = {0}".format(id))
        response = requests.delete("{0}/instance/{1}".format(self.rest_url, id), \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        if response.status_code != 200:
            raise RuntimeError("Error when configuring the instance global parameters : {0}".format(response.text))

    def del_instances_by_client(self, client_id):
        """ Call GET /instance to get all instances
            Then, call del_instance for each instance of the given client_id
            @param client_id: the client id for which we want to delete all the instances
        """
        print(u"Delete all the instances for the client id '{0}'".format(client_id))
        # first, retrieve all the instances
        response = requests.get("{0}/instance/".format(self.rest_url), \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        if response.status_code != 200:
            raise RuntimeError("Error when configuring the instance global parameters : {0}".format(response.text))
        if response.text == "":
            print(u"There is no instance to delete")
            return
        instances = instance = json.loads(response.text)
        for instance in instances:
            #print(u"Id = {0} / Client_id = {1}".format(instance['id'], instance['client_id']))
            if instance['client_id'] == client_id:
                self.del_instance(instance['id'])
        
        


if __name__ == "__main__":

    td = TestDevice()
    #td.create_instance("plugin-diskfree.{0}".format(get_sanitized_hostname()), "avec un accent é comme ça", "diskfree.disk_usage")
    td.create_instance("plugin-diskfree.{0}".format(get_sanitized_hostname()), "test_instance_diskfree", "diskfree.disk_usage")
    td.configure_global_parameters({"instance" : "/home", "interval" : 1})
    #td.del_instance(td.instance_id)
    #td.del_instances_by_client("foo")
    #td.del_instances_by_client("plugin-diskfree.darkstar")

