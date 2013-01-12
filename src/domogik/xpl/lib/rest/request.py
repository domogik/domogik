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
=============

- Process a REST request

Implements
==========

ProcessRequest object



@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.database import DbHelper, DbHelperException
from domogik.xpl.common.helper import HelperError
from domogik.xpl.lib.rest.jsondata import JSonHelper
from domogik.xpl.lib.rest.csvdata import CsvHelper
from domogik.xpl.lib.rest.tail import Tail
from domogik.common.packagemanager import PackageManager, PKG_PART_XPL, PKG_PART_RINOR, PKG_CACHE_DIR, ICON_CACHE_DIR 
from domogik.common.packagexml import PackageException
import time
import urllib
import urlparse
#from socket import gethostname
import re
import traceback
import datetime
import os
import glob
import random
import domogik
import pkgutil
import uuid
import stat
#from stat import * 
import shutil
import mimetypes
from threading import Event
from Queue import Empty
import sys
from subprocess import Popen, PIPE


# Time we wait for answers after a multi host list command
WAIT_FOR_LIST_ANSWERS = 1
WAIT_FOR_PACKAGE_INSTALLATION = 20
WAIT_FOR_DEPENDENCY_CHECK = 30

#### TEMPORARY DATA FOR TEMPORARY FUNCTIONS ############
PING_DURATION = 2
#### END TEMPORARY DATA ################################


class ProcessRequest():
    """ Class for processing a request
    """

    urls = {
	# /account
        'account': {
            '^/account/auth/(?P<login>[a-z]+)/(?P<password>[0-9]+)$':			         '_rest_account_auth',
            '^/account/user/list$':						                 '_rest_account_user_list',
            '^/account/user/list/by-id/(?P<id>[0-9]+)$':                  		         '_rest_account_user_list',
            '^/account/user/add/.*$':						                 '_rest_account_user_add',
            '^/account/user/update/.*$':				                         '_rest_account_user_update',
            '^/account/user/password/.*$':				        	         '_rest_account_user_password',
            '^/account/user/del/(?P<id>[0-9]+)$':    				                 '_rest_account_user_del',
            '^/account/person/list$':						                 '_rest_account_person_list',
            '^/account/person/list/by-id/(?P<id>[0-9]+)$':   			                 '_rest_account_person_list',
            '^/account/person/add/.*$':					                         '_rest_account_person_add',
            '^/account/person/update/.*$':					                 '_rest_account_person_update',
            '^/account/person/password/.*$':				                         '_rest_account_person_password',
            '^/account/person/del/(?P<id>[0-9]+)$':  			                         '_rest_account_person_del',
        },
        # /base
        'base': {
            # /base/device
            '^/base/device/list$':			                                         '_rest_base_device_list',
            '^/base/device/add/.*$':		 	                                         '_rest_base_device_add',
            '^/base/device/update/.*$':		                                                 '_rest_base_device_update',
            '^/base/device/del/(?P<id>[0-9]+)$':		                                 '_rest_base_device_del',
            # /base/device_technology
            '^/base/device_technology/list$':			                                 '_rest_base_device_technology_list',
            '^/base/device_technology/list/by-id/(?P<id>[0-9]+)$':   			         '_rest_base_device_technology_list',
            '^/base/device_technology/add/.*$':		 	                                 '_rest_base_device_technology_add',
            '^/base/device_technology/update/.*$':		                                 '_rest_base_device_technology_update',
            '^/base/device_technology/del/(?P<dt_id>[0-9]+)$':		                         '_rest_base_device_technology_del',
            # /base/device_type
            '^/base/device_type/list$':			                                         '_rest_base_device_type_list',
            '^/base/device_type/add/.*$':		 	                                 '_rest_base_device_type_add',
            '^/base/device_type/update/.*$':		                                         '_rest_base_device_type_update',
            '^/base/device_type/del/(?P<dt_id>[0-9]+)$':		                         '_rest_base_device_type_del',
            # /base/device_usage
            '^/base/device_usage/list$':			                                 '_rest_base_device_usage_list',
            '^/base/device_usage/list/by-name/(?P<name>[a-z0-9]+)$':	                         '_rest_base_device_usage_list',
            '^/base/device_usage/add/.*$':		 	                                 '_rest_base_device_usage_add',
            '^/base/device_usage/update/.*$':		                                         '_rest_base_device_usage_update',
            '^/base/device_usage/del/(?P<du_id>[0-9]+)$':		                         '_rest_base_device_usage_del',
            # /base/feature
            '^/base/feature/list$':			                                         '_rest_base_feature_list',
            '^/base/feature/list/by-id/(?P<id>[0-9]+)$':   			                 '_rest_base_feature_list',
            '^/base/feature/list/by-device_id/(?P<device_id>[0-9]+)$':   			 '_rest_base_feature_list',
        },
        # /command
        'command': {
	    '^/command.*$':                                                                      'rest_command',
        },
        # /event
        'events': {
            '^/events/domogik/new$':						                 '_rest_events_domogik_new',
            '^/events/domogik/get/(?P<ticketid>[0-9]+)$':					 '_rest_events_domogik_get',
            '^/events/domogik/free/(?P<ticket_id>[0-9]+)$':			                 '_rest_events_domogik_free',
            #'^/events/request/new/.*$':					                 'needs a new function',
            '^/events/request/get/(?P<ticket_id>[0-9]+)$':				         '_rest_events_request_get',
            '^/events/request/free/(?P<ticket_id>[0-9]+)$':			                 '_rest_events_request_free',
        },
        # /helper
        'helper': {
            '^/helper/.*$':			                                                 'rest_helper',
        },
        # /host
        'host': {
            '^/host/.*$':			                                                 'rest_host',
        },
        # /log
        'log': {
            '^/log/tail/txt/(?P<host>[a-z]+)/(?P<file>[a-z\.]+)/(?P<number>[0-9]+)/(?P<ofset>[0-9]+)$': '_rest_log_tail_txt',
            '^/log/tail/html/(?P<host>[a-z]+)/(?P<file>[a-z\.]+)/(?P<number>[0-9]+)/(?P<ofset>[0-9]+)$': '_rest_log_tail_html',
        },
        # /package
        'package': {
            '^/package/get-mode$':								 '_rest_package_get_mode',
            '^/package/list-repo$':							         '_rest_package_list_repo',
            '^/package/update-cache$':								 '_rest_package_update_cache',
            '^/package/available/(?P<host>[a-z]+)/(?P<pkg_type>[plugin|external]+)$':		 '_rest_package_available',
            '^/package/installed/(?P<host>[a-z]+)/(?P<pkg_type>[plugin|external]+)$':		 '_rest_package_installed',
            '^/package/dependency/(?P<host>[a-z]+)/(?P<pkg_type>[plugin|external]+)/(?P<id>[^/]+)/(?P<version>[^/]+)$': '_rest_package_dependency',
            '^/package/install/(?P<host>[a-z]+)/(?P<type>[plugin|external]+)/(?P<id>[^/]+)/(?P<version>[^/]+)$': '_rest_package_install',
            '^/package/uninstall/(?P<host>[a-z]+)/(?P<type>[plugin|external]+)/(?P<id>[^/]+)$':  '_rest_package_uninstall',
            '^/package/icon/available/(?P<type>[plugin|external]+)/(?P<id>[^/]+)/(?P<version>[^/]+)$':  '_rest_package_icon_available',
            '^/package/icon/installed/(?P<type>[plugin|external]+)/(?P<id>[^/]+)$':              '_rest_package_icon_installed',
        },
        # /plugin
        'plugin': {
            '^/plugin/list$':                                                                        '_rest_plugin_list',
            '^/plugin/detail/(?P<host>[a-z]+)/(?P<id>[a-z]+)$':                                      '_rest_plugin_detail',
            '^/plugin/dependency/(?P<host>[a-z]+)/(?P<id>[a-z]+)$':                                  '_rest_plugin_dependency',
            '^/plugin/udev-rule/(?P<host>[a-z]+)/(?P<id>[a-z]+)$':                                   '_rest_plugin_udev_rule',
            '^/plugin/(?P<command>enable|disable)/(?P<host>[a-z]+)/(?P<plugin>[a-z]+)$':             '_rest_plugin_enable_disable',
            '^/plugin/(?P<command>start|stop)/(?P<host>[a-z]+)/(?P<plugin>[a-z]+)$':                 '_rest_plugin_start_stop',
            '^/plugin/config/list/by-name/(?P<hostname>[a-z]+)/(?P<id>[a-z]+)$':                         '_rest_plugin_config_list',
            '^/plugin/config/list/by-name/(?P<hostname>[a-z]+)/(?P<id>[a-z]+)/by-key/(?P<key>[a-z0-9]+)$': '_rest_plugin_config_list',
            '^/plugin/config/list/del/(?P<host>[a-z]+)/(?P<id>[a-z]+)$':                             '_rest_plugin_config_del',
            '^/plugin/config/list/del/(?P<host>[a-z]+)/(?P<id>[a-z]+)/by-key/(?P<key>[a-z0-9]+)$':   '_rest_plugin_config_del',
	    '^/plugin/config/set/.*$':								 '_rest_plugin_config_set',
        },
        # /queuecontent
        'queuecontent': {
            '^/queuecontent/.*$':                                                                    'rest_queuecontent',
        },
        # /repo
        'repo': {
            '^/repo/put$':                                                                           '_rest_repo_put',
            '^/repo/get/(?P<file_name>[a-z0-9]+)$':                                                  '_rest_repo_get',
        },
        # /stats
        'stats': {
            '^/stats/(?P<device_id>[0-9]+)/(?P<key>[^/]+)/all$':				     '_rest_stats_all',
            '^/stats/(?P<device_id>[0-9]+)/(?P<key>[^/]+)/latest$':				     '_rest_stats_last',
            '^/stats/(?P<device_id>[0-9]+)/(?P<key>[^/]+)/last/(?P<num>[0-9]+)$':		     '_rest_stats_last',
            '^/stats/(?P<device_id>[0-9]+)/(?P<key>[^/]+)/from/.*$':     		             '_rest_stats_from',
            '^/stats/multi/.*$':								     '_rest_stats_multi',
        },
   }


######
# init namespace
######


    def __init__(self, handler_params, path, command, headers, \
                 send_response, \
                 send_header, \
                 end_headers, \
                 wfile, \
                 rfile, \
                 cb_send_http_response_ok, \
                 cb_send_http_response_404, \
                 cb_send_http_response_error, \
                 cb_send_http_response_text_plain, \
                 cb_send_http_response_text_html):
        """ Create shorter access : self.server.handler_params[0].* => self.*
            First processing on url given
            @param handler_params : parameters given to HTTPHandler
            @param path : path given to HTTP server : /base/area/... for example
            @param command : GET, POST, PUT, OPTIONS, etc
            @param cb_send_http_response_ok : callback for function
                                              REST.send_http_response_ok 
            @param cb_send_http_response_404 : callback for function
                                              REST.send_http_response_404 
            @param cb_send_http_response_error : callback for function
                                              REST.send_http_response_error 
            @param cb_send_http_response_text_plain : callback for function
                                              REST.send_http_response_text_plain
            @param cb_send_http_response_text_html : callback for function
                                              REST.send_http_response_text_html 
        """

        self.handler_params = handler_params
        self.path = path
        self.command = command
        self.headers = headers
        self.send_response = send_response
        self.send_header = send_header
        self.end_headers = end_headers
        # Is there a need for this ?
        #self.copyfile = self.handler_params[0].copyfile
        self.wfile = wfile
        self.rfile = rfile
        self.send_http_response_ok = cb_send_http_response_ok
        self.send_http_response_404 = cb_send_http_response_404
        self.send_http_response_error = cb_send_http_response_error
        self.send_http_response_text_plain = cb_send_http_response_text_plain
        self.send_http_response_text_html = cb_send_http_response_text_html
        self.xpl_cmnd_schema = None
        self._put_filename = None

        # shorter access
        self.get_sanitized_hostname = self.handler_params[0].get_sanitized_hostname
        self._rest_api_version = self.handler_params[0]._rest_api_version
        self.myxpl = self.handler_params[0].myxpl
        self.log = self.handler_params[0].log
        self.log_dm = self.handler_params[0].log_dm
        self._package_path = self.handler_params[0]._package_path
        self._src_prefix = self.handler_params[0]._src_prefix
        self._design_dir = self.handler_params[0]._design_dir
        self._xml_cmd_dir = self.handler_params[0]._xml_cmd_dir
        self._xml_stat_dir = self.handler_params[0]._xml_stat_dir
        self.repo_dir = self.handler_params[0].repo_dir
        self.use_ssl = self.handler_params[0].use_ssl
        self.get_exception = self.handler_params[0].get_exception
        self.log_dir_path = self.handler_params[0].log_dir_path

        self.log.debug("Process request : init")

        self._queue_timeout =  self.handler_params[0]._queue_timeout
        self._queue_size =  self.handler_params[0]._queue_size
        self._queue_command_size =  self.handler_params[0]._queue_command_size
        self._queue_package_size =  self.handler_params[0]._queue_package_size
        self._queue_life_expectancy = self.handler_params[0]._queue_life_expectancy
        self._queue_event_size =  self.handler_params[0]._queue_event_size
        self._get_from_queue = self.handler_params[0]._get_from_queue
        self._put_in_queue = self.handler_params[0]._put_in_queue

        self._queue_package =  self.handler_params[0]._queue_package

        self._queue_system_list =  self.handler_params[0]._queue_system_list
        self._queue_system_detail =  self.handler_params[0]._queue_system_detail
        self._queue_system_start =  self.handler_params[0]._queue_system_start
        self._queue_system_stop =  self.handler_params[0]._queue_system_stop
        self._queue_command =  self.handler_params[0]._queue_command

        self._event_dmg =  self.handler_params[0]._event_dmg
        self._event_requests =  self.handler_params[0]._event_requests

        self.xml =  self.handler_params[0].xml
        self.xml_ko =  self.handler_params[0].xml_ko
        self.xml_date =  self.handler_params[0].xml_date

        self.stat_mgr =  self.handler_params[0].stat_mgr

        self._hosts_list = self.handler_params[0]._hosts_list
        self.get_installed_packages = self.handler_params[0].get_installed_packages
        self._get_installed_packages_from_manager = self.handler_params[0]._get_installed_packages_from_manager

        # global init
        self.jsonp = False
        self.jsonp_cb = ""
        self.csv_export = False

        # package path
        if self._package_path != None:  # package mode
            sys.path = [self._package_path] + sys.path

        # url processing
        #self.path = self.fixurl(self.path)
        #self.path = urllib.unquote(self.path)

        # replace password by "***". 
        path_without_passwd = re.sub("password/[^/]+/", "password/***/", self.path + "/")
        self.log.info("Request : %s" % path_without_passwd)

        # log data manipulation here
        if re.match(".*(add|update|del|set).*", path_without_passwd) is not None:
            self.log_dm.info("REQUEST=%s" % path_without_passwd)

        tab_url = self.path.split("?")
        self.path = tab_url[0]
        if len(tab_url) > 1:
            self.parameters = str(tab_url[1])
            self._parse_options()

        if self.path[-1:] == "/":
            self.path = self.path[0:len(self.path)-1]
        tab_path_quoted = self.path.split("/")
        tab_path = [urllib.unquote(item) for item in tab_path_quoted]

        # Get type of request : /command, /xpl-cmnd, /base, etc
        if len(tab_path) < 2:
            self.rest_type = None
            # Display an information json if no request done in do_for_all_methods
            return
        self.rest_type = tab_path[1].lower()
        if len(tab_path) > 2:
            self.rest_request = tab_path[2:]
        else:
            self.rest_request = []

        # DB Helper
        self._db = DbHelper()

        #### TEMPORARY DATA FOR TEMPORARY FUNCTIONS ############
        self._pinglist = {}

        #### END TEMPORARY DATA ################################

    def fixurl(self, url):
        """ translate url in unicode
            @param url : url to put in unicode
        """
        # turn string into unicode
        if not isinstance(url,unicode):
            url = url.decode('utf8')
    
        # parse it
        parsed = urlparse.urlsplit(url)
    
        # divide the netloc further
        userpass,at,hostport = parsed.netloc.partition('@')
        user,colon1,pass_ = userpass.partition(':')
        host,colon2,port = hostport.partition(':')
    
        # encode each component
        scheme = parsed.scheme.encode('utf8')
        user = urllib.quote(user.encode('utf8'))
        colon1 = colon1.encode('utf8')
        pass_ = urllib.quote(pass_.encode('utf8'))
        at = at.encode('utf8')
        host = host.encode('idna')
        colon2 = colon2.encode('utf8')
        port = port.encode('utf8')
        path = '/'.join(  # could be encoded slashes!
            urllib.quote(urllib.unquote(pce).encode('utf8'),'')
            for pce in parsed.path.split('/')
        )
        query = urllib.quote(urllib.unquote(parsed.query).encode('utf8'),'=&?/')
        fragment = urllib.quote(urllib.unquote(parsed.fragment).encode('utf8'))
    
        # put it back together
        netloc = ''.join((user,colon1,pass_,at,host,colon2,port))
        return urllib.unquote(urlparse.urlunsplit((scheme,netloc,path,query,fragment)))
    
    def do_for_all_methods(self):
        """ Process request
            This function call appropriate functions for processing path
        """
        found = 0
        if self.rest_type == None:
           self.rest_status()
           found = 1 
        else:
            self.parameters = {}
            self.set_parameters(0)
            if self.rest_type in self.urls:
                for k in self.urls[self.rest_type]:
                    m = re.match(k, self.path)
                    if m:
                        found = 1
                        if len( m.groupdict() ) == 0:
                            eval('self.' + self.urls[self.rest_type][k] + '()')
                        else:
                            eval('self.'  + self.urls[self.rest_type][k] + '(' + ', '.join([v+"='"+k2+"'" for (v,k2) in m.groupdict().iteritems()]) + ')')
                        break
        if found == 0:
	    self.log.warning("New url parser does not know url %s" % self.path) 
	    print("New url parser does not know url %s" % self.path) 
            if self.rest_type == "command":
                self.rest_command()
            elif self.rest_type == "stats":
                self.rest_stats()
            elif self.rest_type == "events":
                self.rest_events()
            # commented for security reasons
            #elif self.rest_type == "xpl-cmnd":
            #    self.rest_xpl_cmnd()
            elif self.rest_type == "base":
                self.rest_base()
            elif self.rest_type == "plugin":
                self.rest_plugin()
            elif self.rest_type == "account":
                self.rest_account()
            elif self.rest_type == "queuecontent":
                self.rest_queuecontent()
            elif self.rest_type == "helper":
                self.rest_helper()
            elif self.rest_type == "testlongpoll":
                self.rest_testlongpoll()
            elif self.rest_type == "repo":
                self.rest_repo()
            elif self.rest_type == "scenario":
                self.rest_scenario()
            elif self.rest_type == "package":
                self.rest_package()
            elif self.rest_type == "log":
                self.rest_log()
            elif self.rest_type == "host":
                self.rest_host()
            elif self.rest_type == None:
                self.rest_status()
            else:
                self.send_http_response_error(999, "Type [" + str(self.rest_type) + \
                                          "] is not supported", \
                                          self.jsonp, self.jsonp_cb)


    def _parse_options(self):
        """ Process parameters : ...?param1=val1&param2=val2&....
        """
        self.log.debug("Parse request options : %s" % self.parameters)

        if self.parameters[-1:] == "/":
            self.parameters = self.parameters[0:len(self.parameters)-1]

        # for each debug option
        for opt in self.parameters.split("&"):
            self.log.debug("OPT : %s" % opt)
            tab_opt = opt.split("=")
            opt_key = tab_opt[0]
            if len(tab_opt) > 1:
                opt_value = tab_opt[1]
            else:
                opt_value = None

            # call json specific options
            if opt_key == "callback" and opt_value != None:
                self.log.debug("Option : jsonp mode")
                self.jsonp = True
                self.jsonp_cb = opt_value

            # CSV export format (if available in functions)
            if opt_key == "export" and opt_value == "csv":
                self.log.debug("Option : CSV export")
                self.csv_export = True

            # call debug functions
            if opt_key == "debug-sleep" and opt_value != None:
                self._debug_sleep(opt_value)

            # name for PUT : /repo/put?filename=foo.txt
            if opt_key == "filename" and opt_value != None:
                self._put_filename = opt_value



    def _debug_sleep(self, duration):
        """ Sleep process for 15 seconds
        """
        self.log.debug("Start sleeping for " + str(duration))
        time.sleep(float(duration))
        self.log.debug("End sleeping")





######
# / processing
######

    def rest_status(self):
        """ Send REST status informations
        """
        json_data = JSonHelper("OK", 0, "REST server available")
        json_data.set_data_type("rest")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)

        # Description and parameters
        info = {}
        info["REST_API_version"] = self._rest_api_version
        info["SSL"] = self.use_ssl
        info["Domogik_version"] = self.rest_status_dmg_version()
        info["Sources_version"] = self.rest_status_src_version()
        info["Host"] = self.get_sanitized_hostname()

        # for compatibility with Rest API < 0.6
        info["REST_API_release"] = self._rest_api_version
        info["Domogik_release"] = self.rest_status_dmg_version()
        info["Sources_release"] = self.rest_status_src_version()


        # Xml command files
        command = {}
        xml_info = []
        for key in self.xml:
            xml_info.append(key)
        command["XML_files_loaded"] = xml_info
        command["XML_files_KO"] = self.xml_ko
        command["XML_files_last_load"] = self.xml_date

        # Xml stat files
        stats = {}
        stats["XML_files_loaded"] = self.stat_mgr.get_xml_list()
        stats["XML_files_KO"] = self.stat_mgr.get_xml_ko_list()
        stats["XML_files_last_load"] = self.stat_mgr.get_load_date()

        # Queues stats
        queues = {}
        queues["package_usage"] = "%s/%s" \
            % (self._queue_package.qsize(), int(self._queue_package_size))
        queues["system_list_usage"] = "%s/%s" \
            % (self._queue_system_list.qsize(), int(self._queue_size))
        queues["system_detail_usage"] = "%s/%s" \
            % (self._queue_system_detail.qsize(), int(self._queue_size))
        queues["system_start_usage"] = "%s/%s" \
            % (self._queue_system_start.qsize(), int(self._queue_size))
        queues["system_stop_usage"] = "%s/%s" \
            % (self._queue_system_stop.qsize(), int(self._queue_size))
        queues["command_usage"] = "%s/%s" \
            % (self._queue_command.qsize(), int(self._queue_command_size))

        # Events stats
        events = {}
        events["Number_of_Domogik_events_requests"] = self._event_dmg.count()
        events["Number_of_devices_events_requests"] = self._event_requests.count()
        events["Max_size_for_request_queues"] = int(self._queue_event_size)
        events["Domogik_requests"] = self._event_dmg.list()
        events["Devices_requests"] = self._event_requests.list()

        # Configuration
        conf = [
                {
                    "id" : 0,
                    "key" : "q-timeout",
                    "description" : "Maximum wait time for getting data froma queue",
                    "type" : "Number",
                    "default" : 15,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 1,
                    "key" : "q-size",
                    "description" : "Size for 'classic' queues. You should not have to change this value",
                    "type" : "Number",
                    "default" : 10,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 2,
                    "key" : "q-pkg-size",
                    "description" : "Size for packages management queues. You should not have to change this value",
                    "type" : "Number",
                    "default" : 10,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 3,
                    "key" : "q-cmd-size",
                    "description" : "Size for /command queue",
                    "type" : "Number",
                    "default" : 1000,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 4,
                    "key" : "q-life-exp",
                    "description" : "Life expectancy for a xpl message in queues. You sould not have to change this value",
                    "type" : "Number",
                    "default" : 3,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 5,
                    "key" : "q-sleep",
                    "description" : "Time between each unsuccessfull look for a xpl data in a queue",
                    "type" : "Number",
                    "default" : 0.1,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 6,
                    "key" : "evt-timeout",
                    "description" : "Maximum wait time for a GET request (after event will be closed)",
                    "type" : "Number",
                    "default" : 300,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 7,
                    "key" : "q-evt-timeout",
                    "description" : ">Maximum wait time for getting event from queue",
                    "type" : "Number",
                    "default" : 120,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 8,
                    "key" : "q-evt-size",
                    "description" : "Size for /event queue",
                    "type" : "Number",
                    "default" : 50,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 9,
                    "key" : "q-evt-life-exp",
                    "description" : "Life expectancy for an event in event queues",
                    "type" : "Number",
                    "default" : 5,
                    "element_type" : "item",
                    "optionnal" : "no",
                }
            ] 

        data = {"info" : info, 
                "command" : command,
                "stats" : stats,
                "queue" : queues, 
                "event" : events,
                "configuration" : conf}
        json_data.add_data(data)

        self.send_http_response_ok(json_data.get())


    def rest_status_src_version(self):
        """ Return sources version
        """
        domogik_path = os.path.dirname(domogik.xpl.lib.rest.__file__)
        #subp = Popen("cd %s ; hg log -r tip --template '{branch}.{rev} ({latesttag}) - {date|isodate}'" % domogik_path, shell=True, stdout=PIPE, stderr=PIPE)
        subp = Popen("cd %s ; hg branch | xargs hg log -l1 --template '{branch}.{rev} - {date|isodate}' -b" % domogik_path, shell=True, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = subp.communicate()
        # if hg id has no error, we are using source  repository
        if subp.returncode == 0:
            return "%s" % (stdout)
        # else, we send dmg version
        else:
            return self.rest_status_dmg_version()

    def rest_status_dmg_version(self):
        """ Return Domogik version
        """
        __import__("domogik")
        global_version = sys.modules["domogik"].__version__
        return global_version


######
# /robots.txt processing
######

    def rest_robots_txt(self):
        """ Tell crawlers to go away
        """
        self.send_http_response_ok("# go away\nUser-agent: *\nDisallow: /\n")

######
# /command processing
######

    def rest_command(self):
        """ Process /command url
            - decode request
            - call a xml parser for the technology (self.rest_request[0])
           - send appropriate xPL message on network
        """
        self.log.debug("Process /command")

        ### Check url length
        if len(self.rest_request) < 3:
            json_data = JSonHelper("ERROR", 999, "Url too short for /command")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())
            return

        ### Get parameters
        techno = self.rest_request[0]
        address = self.rest_request[1]
        command = self.rest_request[2]
        if len(self.rest_request) > 3:
            params = self.rest_request[3:]
        else:
            params = None

        self.log.debug("Techno  : %s" % techno)
        self.log.debug("Address : %s" % address)
        self.log.debug("Command : %s" % command)
        self.log.debug("Params  : %s" % str(params))

        ### Get message 
        message = self._rest_command_get_message(techno, address, command, params)

        ### Get listener
        (schema, xpl_type, filters) = self._rest_command_get_listener(techno, address, command)

        ### Send xpl message
        self.myxpl.send(XplMessage(message))

        ### Wait for answer
        if schema != None:
            # get xpl message from queue
            try:
                self.log.debug("Command : wait for answer...")
                msg_cmd = self._get_from_queue(self._queue_command, xpl_type, schema, filters)
            except Empty:
                self.log.debug("Command (%s, %s, %s, %s) : no answer" % (techno, address, command, params))
                json_data = JSonHelper("ERROR", 999, "No data or timeout on getting command response")
                json_data.set_jsonp(self.jsonp, self.jsonp_cb)
                json_data.set_data_type("response")
                self.send_http_response_ok(json_data.get())
                return
    
            self.log.debug("Command : message received : %s" % str(msg_cmd))

        else:
            # no listener defined in xml : don't wait for an answer
            self.log.debug("Command : no listener defined : not waiting for an answer")

        ### REST processing finished and OK
        json_data = JSonHelper("OK")
        json_data.set_data_type("response")
        if schema != None:
            json_data.add_data({"xpl" : str(msg_cmd)})
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())




    def _rest_command_get_message(self, techno, address, command, params):
        """ Generate xpl message for /command
        """ 
        ref = "%s/%s.xml" % (techno, command)
        try:
            xml_data = self.xml[ref]
        except KeyError:
            self.send_http_response_error(999, "No xml file for '%s'" % ref, \
                                          self.jsonp, self.jsonp_cb)
            return

        ### Check xml validity
        if xml_data.getElementsByTagName("technology")[0].attributes.get("id").value != techno:
            self.send_http_response_error(999, "'technology' attribute in xml file must be '%s'" % techno, \
                                          self.jsonp, self.jsonp_cb)
            return
        if xml_data.getElementsByTagName("command")[0].attributes.get("name").value != command:
            self.send_http_response_error(999, "'command' attribute in xml file must be '%s'" % command, \
                                          self.jsonp, self.jsonp_cb)
            return

        ### Get only <command...> part
        xml_command = xml_data.getElementsByTagName("command")[0]

        ### Get data from xml
        # Schema
        schema = xml_command.getElementsByTagName("schema")[0].firstChild.nodeValue
        if xml_command.getElementsByTagName("command-xpl-value") == []:
            has_command_key = False
        else:
            # command key name 
            has_command_key = True
            command_key = xml_command.getElementsByTagName("command-key")[0].firstChild.nodeValue
            # real command value in xpl message
            command_xpl_value = xml_command.getElementsByTagName("command-xpl-value")[0].firstChild.nodeValue

        if xml_command.getElementsByTagName("address-key") == []:
            has_address_key = False
        else:
            #address key name (device)
            has_address_key = True
            address_key = xml_command.getElementsByTagName("address-key")[0].firstChild.nodeValue

        # Parameters
        #get and count parameters in xml file
        parameters = xml_command.getElementsByTagName("parameters")[0]
        #do the association between url and xml
        parameters_value = {}
        for param in parameters.getElementsByTagName("parameter"):
            key = param.attributes.get("key").value
            loc = param.attributes.get("location")
            static_value = param.attributes.get("value")
            if static_value is None:
                if loc is None:
                    loc.value = 0
                if params == None:
                    value = None
                else:
                    value = params[int(loc.value) - 1]
            else:
                value = static_value.value
            if type(value).__name__ == "str":
                value = unicode(urllib.unquote(value), "UTF-8")
            parameters_value[key] = value

        ### Create xpl message
        msg = """xpl-cmnd
{
hop=1
source=xpl-rest.domogik
target=*
}
%s
{
""" % (schema)
        if has_command_key == True:
            msg += "%s=%s\n" % (command_key, command_xpl_value)
        if has_address_key == True:
            msg += "%s=%s\n" % (address_key, address)
        for m_param in parameters_value.keys():
            msg += "%s=%s\n" % (m_param, parameters_value[m_param])
        msg += "}"
        return msg




    def _rest_command_get_listener(self, techno, address, command):
        """ Create listener for /command 
        """
        xml_data = self.xml["%s/%s.xml" % (techno, command)]

        ### Get only <command...> part
        # nothing to do, tests have be done in get_command

        xml_listener = xml_data.getElementsByTagName("listener")[0]

        ### Get data from xml
        # Schema
        try:
            schema = xml_listener.getElementsByTagName("schema")[0].firstChild.nodeValue
        except IndexError:
            # no schema data : we suppose we have <listener/>
            # TODO : do it in a better way than using try: except:
            return None, None, None

        # xpl type
        xpl_type = xml_listener.getElementsByTagName("xpltype")[0].firstChild.nodeValue

        # Filters
        filters = xml_listener.getElementsByTagName("filter")[0]
        filters_value = {}
        for my_filter in filters.getElementsByTagName("key"):
            name = my_filter.attributes.get("name").value
            value = my_filter.attributes.get("value").value
            if value == "@address@":
                value = address
            filters_value[name] = value

        return schema, xpl_type, filters_value




######
# /stats processing
######

    def rest_stats(self):
        """ Get stats in database
            - Decode and check URL format
            - call the good fonction to get stats from database
        """
        self.log.debug("Process stats request")
        # parameters initialisation
        self.parameters = {}

        # Check url length
        if len(self.rest_request) < 3:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return


        ### multi ####################################
        if self.rest_request[0] == "multi":
            self._rest_stats_multi()
            return

        else:
            device_id = self.rest_request[0]
            key = self.rest_request[1]

            # Replace wildcard value by None value
            if device_id=='*':
                device_id = None
            if key=='*':
                key = None

        ### all ######################################
        if self.rest_request[2] == "all":
            self._rest_stats_all(device_id, key)

        ### latest ###################################
        elif self.rest_request[2] == "latest":
            self._rest_stats_last(device_id, key)

        ### last #####################################
        elif self.rest_request[2] == "last":
            if len(self.rest_request) < 4:
                self.send_http_response_error(999, "Wrong syntax for %s" % self.rest_request[2], self.jsonp, self.jsonp_cb)
                return
            self._rest_stats_last(device_id, key, int(self.rest_request[3]))

        ### from #####################################
        elif self.rest_request[2] == "from":
            if len(self.rest_request) < 4:
                self.send_http_response_error(999, "Wrong syntax for %s" % self.rest_request[2], self.jsonp, self.jsonp_cb)
                return
            offset = 2
            if self.set_parameters(offset):
                self._rest_stats_from(device_id, key)
            else:
                self.send_http_response_error(999, "Error in parameters", \
                                              self.jsonp, self.jsonp_cb)


        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return


    def _rest_stats_multi(self):
        """ Get the last values for all couples device/key in database
        """

        json_data = JSonHelper("OK")
        json_data.set_data_type("stats")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        idx = 1
        while idx < len(self.rest_request):
            data = None
            for data in self._db.list_last_n_stats_of_device(self.rest_request[idx], self.rest_request[idx+1],  1):
                setattr(data, "exists", "True")
                json_data.add_data(data)
            if data == None:
                # first, check if the device exists
                if self._db.get_device(self.rest_request[idx]):
                    json_data.add_data({"device_id" : self.rest_request[idx], \
                                        "exists" : True})
                else:
                    json_data.add_data({"device_id" : self.rest_request[idx], \
                                        "exists" : False})
            idx += 2
        self.send_http_response_ok(json_data.get())


    def _rest_stats_all(self, device_id, key):
        """ Get all values for device/key in database
             @param device_id : device id
             @param key : key for device
        """
        # TODO

        json_data = JSonHelper("OK")
        json_data.set_data_type("stats")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        for data in self._db.list_device_stats(device_id,key):
            # TODO : filter by key
            json_data.add_data(data)
        self.send_http_response_ok(json_data.get())



    def _rest_stats_last(self, device_id, key, num = 1):
        """ Get the last values for device/key in database
             @param device_id : device id
             @param key : key for device
             @param num : number of data to return
        """

        json_data = JSonHelper("OK")
        json_data.set_data_type("stats")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        for data in self._db.list_last_n_stats_of_device(device_id, key,  num):
            json_data.add_data(data)
        self.send_http_response_ok(json_data.get())



    def _rest_stats_from(self, device_id, key):
        """ Get the values for device/key in database for an start time to ...
             @param device_id : device id
             @param key : key for device
             @param others params : will be get with get_parameters (dynamic params)
        """

        st_from = float(self.get_parameters("from"))
        st_to = self.get_parameters("to")
        if st_to != None:
            st_to = float(st_to)
        st_interval = self.get_parameters("interval")
        if st_interval != None:
            st_interval = st_interval.lower()
        st_selector = self.get_parameters("selector")
        if st_selector != None:
            st_selector = st_selector.lower()

        if self.csv_export == False:
            json_data = JSonHelper("OK")
            json_data.set_data_type("stats")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        else:
            csv_data = CsvHelper()
        values = []
        if st_interval != None and st_selector != None:
            data = self._db.filter_stats_of_device_by_key(device_id,
                                                               key,
                                                               st_from,
                                                               st_to,
                                                               st_interval,
                                                               st_selector)
            if self.csv_export == False:
                json_data.add_data({"values" : data["values"],
                                    "global_values" : data["global_values"],
                                    "key" : key, "device_id" : device_id})
            else:
                for my_tuple in data["values"]:
                    if st_interval == "year":
                        csv_data.add_data("%s;%s" % (my_tuple[0],
                                                                 my_tuple[1]))
                    elif st_interval == "month":
                        csv_data.add_data("%s-%s;%s" % (my_tuple[0],
                                                                 my_tuple[1],
                                                                 my_tuple[2]))
                    elif st_interval == "week":
                        csv_data.add_data("%s-%s;%s" % (my_tuple[0],
                                                                 my_tuple[1],
                                                                 my_tuple[2]))
                    elif st_interval == "day":
                        csv_data.add_data("%s-%s-%s;%s" % (my_tuple[0],
                                                                 my_tuple[1],
                                                                 my_tuple[3],
                                                                 my_tuple[4]))
                    elif st_interval == "hour":
                        csv_data.add_data("%s-%s-%s %s;%s" % (my_tuple[0],
                                                                 my_tuple[1],
                                                                 my_tuple[3],
                                                                 my_tuple[4],
                                                                 my_tuple[5]))
                    elif st_interval == "minute":
                        csv_data.add_data("%s-%s-%s %s:%s;%s" % (my_tuple[0],
                                                                 my_tuple[1],
                                                                 my_tuple[3],
                                                                 my_tuple[4],
                                                                 my_tuple[5],
                                                                 my_tuple[6]))
        else:
            for data in self._db.list_stats_of_device_between_by_key(key, device_id, st_from, st_to):
                values.append(data) 
            if self.csv_export == False:
                json_data.add_data({"values" : values, "key" : key, "device_id" : device_id})
            else:
                for my_value in values:
                    csv_data.add_data("%s;%s" % (my_value.date,
                                                 my_value.value))

        if self.csv_export == False:
            self.send_http_response_ok(json_data.get())
        else:
            self.send_http_response_ok(csv_data.get())
    



######
# /events processing
######

    def rest_events(self):
        """ Events processing
        """
        self.log.debug("Process events request")

        # Check url length
        if len(self.rest_request) < 2:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### domogik  ######################################
        if self.rest_request[0] == "domogik":

            #### new
            if self.rest_request[1] == "new":
                self._rest_events_domogik_new()

            #### get
            elif self.rest_request[1] == "get" and len(self.rest_request) == 3:
                self._rest_events_domogik_get(self.rest_request[2])

            #### free
            elif self.rest_request[1] == "free" and len(self.rest_request) == 3:
                self._rest_events_domogik_free(self.rest_request[2])

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### request  ######################################
        if self.rest_request[0] == "request":

            #### new
            if self.rest_request[1] == "new":
                new_idx = 2
                device_id_list = []
                while new_idx < len(self.rest_request):
                    try:
                        device_id_list.append(int(self.rest_request[new_idx]))
                    except ValueError:
                        self.send_http_response_error(999, "Bad value for device id '%s'" % self.rest_request[new_idx], self.jsonp, self.jsonp_cb)
                        return
                        
                    new_idx += 1
                if new_idx == 2:
                    self.send_http_response_error(999, "No device id given", self.jsonp, self.jsonp_cb)
                    return
                self._rest_events_request_new(device_id_list)

            #### get
            elif self.rest_request[1] == "get" and len(self.rest_request) == 3:
                self._rest_events_request_get(self.rest_request[2])

            #### free
            elif self.rest_request[1] == "free" and len(self.rest_request) == 3:
                self._rest_events_request_free(self.rest_request[2])

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return

        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return


    def _rest_events_domogik_new(self):
        """ Create new event request and send data for event
        """
        ticket_id = self._event_dmg.new()
        data = self._event_dmg.get(ticket_id)
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("event")
        json_data.add_data(data)
        self.send_http_response_ok(json_data.get())

    def _rest_events_domogik_get(self, ticket_id):
        """ Get data from event associated to ticket id
            @param ticket_id : ticket id
        """
        data = self._event_dmg.get(ticket_id)
        if data == False:
            json_data = JSonHelper("ERROR", 999, "Error in getting event in queue")
        else:
            json_data = JSonHelper("OK")
            json_data.set_data_type("event")
            json_data.add_data(data)
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())

    def _rest_events_domogik_free(self, ticket_id):
        """ Free event queue for ticket id
            @param ticket_id : ticket id
        """
        if self._event_dmg.free(ticket_id):
            json_data = JSonHelper("OK")
        else:
            json_data = JSonHelper("ERROR", 999, "Error when trying to free queue for event")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())


    def _rest_events_request_new(self, device_id_list):
        """ Create new event request and send data for event
            @param device_id_list : list of devices to check for events
        """
        ticket_id = self._event_requests.new(device_id_list)
        data = self._event_requests.get(ticket_id)
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("event")
        json_data.add_data(data)
        self.send_http_response_ok(json_data.get())

    def _rest_events_request_get(self, ticket_id):
        """ Get data from event associated to ticket id
            @param ticket_id : ticket id
        """
        data = self._event_requests.get(ticket_id)
        if data == False:
            json_data = JSonHelper("ERROR", 999, "Error in getting event in queue")
        else:
            json_data = JSonHelper("OK")
            json_data.set_data_type("event")
            json_data.add_data(data)
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())

    def _rest_events_request_free(self, ticket_id):
        """ Free event queue for ticket id
            @param ticket_id : ticket id
        """
        if self._event_requests.free(ticket_id):
            json_data = JSonHelper("OK")
        else:
            json_data = JSonHelper("ERROR", 999, "Error when trying to free queue for event")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())

######
# /xpl-cmnd processing
######

    def rest_xpl_cmnd(self):
        """ Send xPL message given in REST url
            - Decode and check URL
            - Send message
        """
        self.log.debug("Send xpl message")

        if len(self.rest_request) == 0:
            self.send_http_response_error(999, "Schema not given", self.jsonp, self.jsonp_cb)
            return
        self.xpl_cmnd_schema = self.rest_request[0]

        # Init xpl message
        message = XplMessage()
        message.set_type('xpl-cmnd')
        message.set_schema(self.xpl_cmnd_schema)
  
        iii = 0
        for val in self.rest_request:
            # We pass target and schema
            if iii > 0:
                # Parameter
                if iii % 2 == 1:
                    param = val
                # Value
                else:
                    value = val
                    message.add_data({param : value})
            iii = iii + 1

        # no parameters
        if iii == 1:
            self.send_http_response_error(999, "No parameters specified", self.jsonp, self.jsonp_cb)
            return
        # no value for last parameter
        if iii % 2 == 0:
            self.send_http_response_error(999, "Value missing for last parameter", self.jsonp, self.jsonp_cb)
            return

        self.log.debug("Send message : %s" % str(message))
        self.myxpl.send(message)

        # REST processing finished and OK
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())




######
# /base processing
######

    def rest_base(self):
        """ Get data in database
            - Decode and check URL format
            - call the good fonction to get data from database
        """
        self.log.debug("Process base request")
        # parameters initialisation
        self.parameters = {}

        # Check url length
        if len(self.rest_request) < 2:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### device_usage #############################
        if self.rest_request[0] == "device_usage":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_usage_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-name":
                        self._rest_base_device_usage_list(self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_usage_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_usage_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_device_usage_del(du_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### device_type ##############################
        elif self.rest_request[0] == "device_type":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_type_list()
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### feature ######################
        elif self.rest_request[0] == "feature":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_feature_list()
                elif len(self.rest_request) == 4 and self.rest_request[2] == "by-id":
                    self._rest_base_feature_list(id = self.rest_request[3])
                elif len(self.rest_request) == 4 and self.rest_request[2] == "by-device_id":
                    self._rest_base_feature_list(device_id = self.rest_request[3])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return



        ### device technology ##########################
        elif self.rest_request[0] == "device_technology":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_technology_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_base_device_technology_list(id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_technology_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_technology_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_device_technology_del(dt_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return






        ### device #####################################
        elif self.rest_request[0] == "device":
            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_list()
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_device_del(id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return



    def set_parameters(self, offset):
        """ define parameters as key => value
            @param offset : number of item to pass before getting key/values in REST request
            @return value if OK. False if no parameters or missing value
        """
        iii = 0
        while offset + iii < len(self.rest_request):
            key = self.rest_request[offset + iii]
            if offset + iii + 1 < len(self.rest_request):
                value = self.rest_request[offset + iii + 1]
            else:
                # wrong number of arguments
                return False
            # specific process for False/True
            #if value == "False" or value == "false":
            #    self.parameters[key] = False
            #elif value == "True" or value == "true":
            #    self.parameters[key] = True
            #else:
            #    self.parameters[key] = value
            self.parameters[key] = value
            iii += 2
        # no parameters
        if iii == 0:
            return False
        # ok
        else:
            return True



    def get_parameters(self, name):
        """ Getter for parameters. If parameter doesn't exist, return None
            @param name : name of parameter to get
            @return parameter value or None if parameter doesn't exist
        """
        try:
            data = self.parameters[name].strip()
            if data == None or data == "None":
                return None
            elif data == "True":
                return True
            elif data == "False":
                return False
            else:
                return data
                #return unicode(urllib.unquote(data), sys.stdin.encoding)
                #return unicode(urllib.unquote(data), "UTF-8")
        except KeyError:
            return None



    def to_date(self, date):
        """ Transform YYYYMMDD date in datatime object
                      YYYYMMDD-HHMM ....
            @param date : date
        """
        if date == None:
            return None
        my_date = None
        if len(date) == 8:  # YYYYMDD
            year = int(date[0:4])
            month = int(date[4:6])
            day = int(date[6:8])
            try:
                my_date = datetime.date(year, month, day)
            except:
                self.send_http_response_error(999, self.get_exception(), self.jsonp, self.jsonp_cb)
        elif len(date) == 13:  # YYYYMMDD-HHMM
            year = int(date[0:4])
            month = int(date[4:6])
            day = int(date[6:8])
            hour = int(date[9:11])
            minute = int(date[11:13])
            try:
                my_date = datetime.datetime(year, month, day, hour, minute)
            except:
                self.send_http_response_error(999, self.get_exception(), self.jsonp, self.jsonp_cb)
        else:
            self.send_http_response_error(999, "Bad date format (YYYYMMDD or YYYYMMDD-HHMM required", self.jsonp, self.jsonp_cb)
        return my_date

######
# /base/device_usage processing
######

    def _rest_base_device_usage_list(self, name = None):
        """ list device usages
            @param name : name of device usage
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        if name == None:
            for device_usage in self._db.list_device_usages():
                json_data.add_data(device_usage)
        else:
            device_usage = self._db.get_device_usage_by_name(name)
            if device_usage is not None:
                json_data.add_data(device_usage)
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_usage_add(self):
        """ add device_usage
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        try:
            device_usage = self._db.add_device_usage(self.get_parameters("id"), \
                                                     self.get_parameters("name"), \
                                                     self.get_parameters("description"), \
                                                     self.get_parameters("default_options"))
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_usage_update(self):
        """ update device usage
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        try:
            device_usage = self._db.update_device_usage(self.get_parameters("id"), \
                                                        self.get_parameters("name"), \
                                                        self.get_parameters("description"), \
                                                        self.get_parameters("default_options"))
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




    def _rest_base_device_usage_del(self, du_id=None):
        """ delete device usage
            @param du_id : device usage id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        try:
            device_usage = self._db.del_device_usage(du_id)
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



######
# /base/device_type processing
######

    def _rest_base_device_type_list(self):
        """ list device types
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        for device_type in self._db.list_device_types():
            json_data.add_data(device_type)
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_type_add(self):
        """ add device type
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        try:
            device_type = self._db.add_device_type(self.get_parameters("id"), \
                                                   self.get_parameters("name"), \
                                                   self.get_parameters("technology_id"), \
                                                   self.get_parameters("description"))
            json_data.add_data(device_type)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_type_update(self):
        """ update device_type
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        try:
            b = self._db.update_device_type(self.get_parameters("id"), \
                                               self.get_parameters("name"), \
                                               self.get_parameters("technology_id"), \
                                               self.get_parameters("description"))
            json_data.add_data(b)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




    def _rest_base_device_type_del(self, dt_id=None):
        """ delete device_type
            @param dt_id : device type id to delete
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        try:
            device_type = self._db.del_device_type(dt_id)
            json_data.add_data(device_type)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




######
# /base/feature processing
######

    def _rest_base_feature_list(self, id = None, device_id = None):
        """ list device type features
            @param id : feature id
            @param device_id : id of device 
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature")
        if id == None and device_id == None:
            for feature in self._db.list_device_features():
                json_data.add_data(feature)
        elif id != None:
            feature = self._db.get_device_feature_by_id(id)
            json_data.add_data(feature)
        elif device_id != None:
            for feature in self._db.list_device_features_by_device_id(device_id):
                json_data.add_data(feature)
        self.send_http_response_ok(json_data.get())





######
# /base/device_technology processing
######

    def _rest_base_device_technology_list(self, id = None):
        """ list device technologies
            @param name : device technology name
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        if id == None:
            for device_technology in self._db.list_device_technologies():
                json_data.add_data(device_technology)
        else:
            device_technology = self._db.get_device_technology_by_id(id)
            if device_technology is not None:
                json_data.add_data(device_technology)
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_technology_add(self):
        """ add device technology
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        try:
            device_technology = self._db.add_device_technology(self.get_parameters("name"), \
                                                                  self.get_parameters("description"))
            json_data.add_data(device_technology)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_technology_update(self):
        """ update device technology
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        try:
            device_technology = self._db.update_device_technology(self.get_parameters("id"), \
                                                                  self.get_parameters("name"), \
                                                                  self.get_parameters("description"))
            json_data.add_data(device_technology)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_technology_del(self, dt_id=None):
        """ delete device technology
            @param dt_id : device tehcnology id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        try:
            device_technology = self._db.del_device_technology(dt_id)
            json_data.add_data(device_technology)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())






######
# /base/device processing
######

    def _rest_base_device_list(self):
        """ list devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        for device in self._db.list_devices():
            json_data.add_data(device, exclude=['device_stats'])
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_add(self):
        """ add devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        try:
            device = self._db.add_device(self.get_parameters("name"), \
                                         self.get_parameters("address"), \
                                         self.get_parameters("type_id"), \
                                         self.get_parameters("usage_id"), \
                                         self.get_parameters("description"), \
                                         self.get_parameters("reference"))
            json_data.add_data(device)
        except DbHelperException as e:
            json_data.set_error(code = 999, description = e.value)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_update(self):
        """ update devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        try:
            device = self._db.update_device(self.get_parameters("id"), \
                                         self.get_parameters("name"), \
                                         self.get_parameters("address"), \
                                         self.get_parameters("usage_id"), \
                                         self.get_parameters("description"), \
                                         self.get_parameters("reference"))
            json_data.add_data(device)
        except DbHelperException as e:
            json_data.set_error(code = 999, description = e.value)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_del(self, id):
        """ delete device 
            @param id : device id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        try:
            device = self._db.del_device(id)
            json_data.add_data(device)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())

######
# /plugin processing
######

    def rest_plugin(self):
        """ /plugin processing
        """
        self.log.debug("Plugin action")

        # parameters initialisation
        self.parameters = {}

        if len(self.rest_request) < 1:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### list ######################################
        if self.rest_request[0] == "list":

            if len(self.rest_request) == 1:
                self._rest_plugin_list()
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### detail ####################################
        elif self.rest_request[0] == "detail":
            if len(self.rest_request) < 3:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_plugin_detail(self.rest_request[2], self.rest_request[1])

        ### dependency ###############################
        elif self.rest_request[0] == "dependency":
            if len(self.rest_request) == 3:
                self._rest_plugin_dependency(self.rest_request[1],
                                           self.rest_request[2])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### udev-rule #################################
        elif self.rest_request[0] == "udev-rule":
            if len(self.rest_request) == 3:
                self._rest_plugin_udev_rule(self.rest_request[1],
                                           self.rest_request[2])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### enable ####################################
        elif self.rest_request[0] == "enable" \
          or self.rest_request[0] == "disable":
            if len(self.rest_request) < 3:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_plugin_enable_disable(host =  self.rest_request[1], \
                                   plugin = self.rest_request[2],
                                   command = self.rest_request[0])

        ### start / stop ##############################
        elif self.rest_request[0] == "start" \
          or self.rest_request[0] == "stop":
            if len(self.rest_request) < 3:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_plugin_start_stop(plugin =  self.rest_request[2], \
                                   command = self.rest_request[0],
                                   host = self.rest_request[1])


        ### plugin config ############################
        elif self.rest_request[0] == "config":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_plugin_config_list()
                elif len(self.rest_request) == 4 or len(self.rest_request) == 6:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 5:
                    if self.rest_request[2] == "by-name":
                        self._rest_plugin_config_list(id=self.rest_request[4], hostname=self.rest_request[3])
                elif len(self.rest_request) == 7:
                    if self.rest_request[2] == "by-name" and self.rest_request[5] == "by-key":
                        self._rest_plugin_config_list(id = self.rest_request[4], hostname=self.rest_request[3], key = self.rest_request[6])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### set
            elif self.rest_request[1] == "set":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_plugin_config_set()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)


            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 4:
                    self._rest_plugin_config_del(id=self.rest_request[3], hostname=self.rest_request[2])
                elif len(self.rest_request) == 6:
                    if self.rest_request[4] == "by-key":
                        self._rest_plugin_config_del_key(id=self.rest_request[3], hostname=self.rest_request[2], key=self.rest_request[5])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)


            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return

        ### others ####################################
        else:
            self.send_http_response_error(999, "Bad operation for /plugin", self.jsonp, self.jsonp_cb)
            return





    def _rest_plugin_list(self):
        """ Send a xpl message to manager to get plugin list
            Display this list as json
        """
        self.log.debug("Plugin : ask for plugin list")

        ### Send xpl message to get list
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.system")
        message.add_data({"command" : "list"})
        message.add_data({"host" : "*"})
        self.myxpl.send(message)

        ### Wait for answer
        # get xpl message from queue
        # make a time loop of one second after first xpl-trig reception
        messages = []
        try:
            # Get first answer for command
            self.log.debug("Plugin list : wait for first answer...")
            messages.append(self._get_from_queue(self._queue_system_list, "xpl-trig", "domogik.system"))
            # after first message, we start to listen for other messages 
            self.log.debug("Plugin list : wait for other answers during '%s' seconds..." % WAIT_FOR_LIST_ANSWERS)
            max_time = time.time() + WAIT_FOR_LIST_ANSWERS
            while time.time() < max_time:
                try:
                    message = self._get_from_queue(self._queue_system_list, "xpl-trig", "domogik.system", timeout = WAIT_FOR_LIST_ANSWERS)
                    messages.append(message)
                    self.log.debug("Plugin list : get one answer from '%s'" % message.data["host"])
                except Empty:
                    self.log.debug("Plugin list : empty queue")
                    pass
            self.log.debug("Plugin list : end waiting for answers")
        except Empty:
            self.log.debug("Plugin list : no answer")
            json_data = JSonHelper("ERROR", 999, "No data or timeout on getting plugin list")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("plugin")
            self.send_http_response_ok(json_data.get())
            return

        self.log.debug("Plugin list : messages received : %s" % str(messages))
        
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("plugin")

        # process messages
        host_list = {}
        external_list = {} # dedicated list for external members
        for message in messages:
            cmd = message.data['command']
            host = message.data["host"]

            # this erase any previous data for a given host to avoid
            # duplicate entries
            host_list[host] = []
    
            idx = 0
            loop_again = True
            while loop_again:
                try:
                    plg_name = message.data["plugin"+str(idx)+"-name"]
                    plg_type = message.data["plugin"+str(idx)+"-type"]
                    #plg_description = message.data["plugin"+str(idx)+"-desc"]
                    plg_technology = message.data["plugin"+str(idx)+"-techno"]
                    plg_status = message.data["plugin"+str(idx)+"-status"]
                    plg_host = message.data["plugin"+str(idx)+"-host"]
                    plugin_data = ({"id" : plg_name, 
                                    "technology" : plg_technology, 
                                    #"description" : plg_description, 
                                    "status" : plg_status, 
                                    "type" : plg_type, 
                                    "host" : plg_host})
                    if plg_type == "plugin":
                        host_list[plg_host].append(plugin_data)
                    elif plg_type == "external":
                        if not external_list.has_key(plg_host):
                            external_list[plg_host] = []
                        external_list[plg_host].append(plugin_data)

                    idx += 1
                except KeyError:
                    loop_again = False
        for host_name in host_list:
            json_data.add_data({"host" : host_name, 
                                "list" : host_list[host_name]})   
        for host_name in external_list:
            json_data.add_data({"host" : host_name, 
                                "list" : external_list[host_name]})   
        self.send_http_response_ok(json_data.get())



    def _rest_plugin_detail(self, id, host = None):
        """ Send a xpl message to manager to get plugin list
            Display this list as json
            @param id : name of plugin
        """
        if host == None:
            host = self.get_sanitized_hostname()
        self.log.debug("Plugin : ask for plugin detail : %s on %s." % (id, host))

        ### Send xpl message to get detail
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.system")
        message.add_data({"command" : "detail"})
        message.add_data({"plugin" : id})
        message.add_data({"host" : host})
        self.myxpl.send(message)

        ### Wait for answer
        # get xpl message from queue
        try:
            self.log.debug("Plugin : wait for answer...")
            # in filter, "%" means, that we check for something starting with name
            message = self._get_from_queue(self._queue_system_detail, "xpl-trig", "domogik.system", filter_data = {"host" : host, "command" : "detail", "plugin" : id + "%"})
        except Empty:
            json_data = JSonHelper("ERROR", 999, "No data or timeout on getting plugin detail for %s" % id)
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("plugin")
            self.send_http_response_ok(json_data.get())
            return

        self.log.debug("Plugin : message received : %s" % str(message))

        # process message
        cmd = message.data['command']
        host = message.data["host"]
        id = message.data["plugin"]
        try:
            error = message.data["error"]
            self.send_http_response_error(999, "Error on detail request : %s" % error,
                                          self.jsonp, self.jsonp_cb)
            return
        except:
            # no error, everything is alright
            pass 
        my_type = message.data["type"]
        do_loop = True
        description = ""
        idx = 0
        while do_loop:
            try:
                description += message.data["description%s" % idx]
            except KeyError:
                do_loop = False
            idx += 1
        technology = message.data["technology"]
        status = message.data["status"]
        version = message.data["version"]
        documentation = message.data["documentation"]
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("plugin")

        idx = 0
        loop_again = True
        config_data = []
        ### configuration for type = plugin
        if my_type == "plugin":
            while loop_again:
                try:
                    my_interface = message.data["cfg"+str(idx)+"-int"]
                    my_key = message.data["cfg"+str(idx)+"-key"]
                    my_type = message.data["cfg"+str(idx)+"-type"]
                    my_desc = message.data["cfg"+str(idx)+"-desc"]
                    my_default = message.data["cfg"+str(idx)+"-default"]
                    optionskey = "cfg"+str(idx)+"-options"
                    if message.data.has_key(optionskey):
                        my_options = message.data[optionskey]
                    else:
                        my_options = ""
                    optkey = "cfg"+str(idx)+"-opt"
                    if message.data.has_key(optkey):
                        my_optionnal = message.data[optkey]
                    else:
                        my_optionnal = "no"
                    # simple configuration element. 
                    #   "None" because it cames from xpl message
                    if my_interface == "no":
                        config_data.append({"id" : idx+1, 
                                            "optionnal" : my_optionnal,
                                            "element_type" : "item",
                                            "key" : my_key,
                                            "type" : my_type,
                                            "description" : my_desc,
                                            "options": my_options,
                                            "default" : my_default})
                    # interface configuration element
                    else:
                        # search if group already defined
                        found = False
                        for group in config_data:
                            # found
                            if group["element_type"] == "group":
                                found = True
                                group["elements"].append({"id" : idx+1, 
                                              "optionnal" : my_optionnal,
                                              "key" : my_key,
                                              "type" : my_type,
                                              "description" : my_desc,
                                              "options": my_options,
                                              "default" : my_default})
                        # not found
                        if found == False:
                            config_data.append({"element_type" : "group",
                                                "elements" : [
                                                       {"id" : idx+1,
                                                        "optionnal" : my_optionnal,
                                                        "key" : my_key,
                                                        "type" : my_type,
                                                        "description" : my_desc,
                                            		"options": my_options,
                                                        "default" : my_default
                                                       }]})
                    idx += 1
                except:
                    loop_again = False

        ### configuration for type = external
        if my_type == "external":
            while loop_again:
                try:
                    key = message.data["cfg"+str(idx)+"-key"]
                    value = message.data["cfg"+str(idx)+"-value"]
                    config_data.append({"id" : idx+1, 
                                        "key" : key,
                                        "value" : value})
                    idx += 1
                except:
                    loop_again = False

        json_data.add_data({"id" : id, "technology" : technology, "description" : description, "status" : status, "host" : host, "version" : version, "documentation" : documentation, "configuration" : config_data})
        self.send_http_response_ok(json_data.get())


    def _rest_plugin_dependency(self, host, id):
        """ Send a xpl message to check python dependencies
            @param host : host targetted
            @param id : id of package
            Return status of each dependency as json
        """
        self.log.debug("Plugin : ask for getting and checking dependencies")

        ### Send xpl message to check python dependencies on host
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.package")
        message.add_data({"command" : "get-dependencies"})
        message.add_data({"host" : host})
        message.add_data({"id" : id})
        message.add_data({"type" : "plugin"})
        self.myxpl.send(message)


        ### Wait for answer
        # get xpl message from queue
        messages = []
        try:
            self.log.debug("Plugin get dependencies : wait for answer...")
            message = self._get_from_queue(self._queue_package, 
                                           "xpl-trig", 
                                           "domogik.package", 
                                           filter_data = {"command" : "get-dependencies", "host" : host, "id" : id, "type" : "plugin"},
                                           timeout = WAIT_FOR_DEPENDENCY_CHECK)
        except Empty:
            self.log.debug("Plugin get dependencies : no answer")
            self.send_http_response_error(999, "No data or timeout on getting dependencies",
                                          self.jsonp, self.jsonp_cb)
            return

        self.log.debug("Package get dependencies : message receive : %s" % str(message))
        
        # process message
        if message.data.has_key('error'):
            self.send_http_response_error(999, "Error : %s" % message.data['error'], self.jsonp, self.jsonp_cb)
            return
        else:
            idx = 0
            loop_again = True
            dep_list = []
            while loop_again:
                try:
                    my_id = message.data["dep%s-id" % idx]
                    my_type = message.data["dep%s-type" % idx]
                    dep_list.append({"id" : my_id, "type" : my_type})
                    idx += 1
                except:
                    loop_again = False

        self._rest_get_dependency(host, "plugin", dep_list)


    def _rest_plugin_udev_rule(self, host, id):
        """ Send a xpl message to get udev rules for the plugin
            @param host : host targetted
            @param id : id of plugin
            Return status of each dependency as json
        """
        self.log.debug("Plugin : ask for getting udev rules")

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("udev-rule")

        ### Send xpl message to check python dependencies on host
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.package")
        message.add_data({"command" : "get-udev-rules"})
        message.add_data({"host" : host})
        message.add_data({"id" : id})
        message.add_data({"type" : "plugin"})
        self.myxpl.send(message)


        ### Wait for answer
        # get xpl message from queue
        messages = []
        try:
            self.log.debug("Plugin get udev rules : wait for answer...")
            message = self._get_from_queue(self._queue_package, 
                                           "xpl-trig", 
                                           "domogik.package", 
                                           filter_data = {"command" : "get-udev-rules", "host" : host, "id" : id, "type" : "plugin"},
                                           timeout = WAIT_FOR_DEPENDENCY_CHECK)
        except Empty:
            self.log.debug("Plugin get udev rules : no answer")
            self.send_http_response_error(999, "No data or timeout on getting udev rules",
                                          self.jsonp, self.jsonp_cb)
            return

        self.log.debug("Package get udev rules : message receive : %s" % str(message))
        
        # process message
        if message.data.has_key('error'):
            self.send_http_response_error(999, "Error : %s" % message.data['error'], self.jsonp, self.jsonp_cb)
            return
        else:
            idx = 0
            loop_again = True
            rule_list = []
            while loop_again:
                try:
                    model = message.data["rule%s-model" % idx]
                    description = message.data["rule%s-desc" % idx]
                    filename = message.data["rule%s-filename" % idx]
                    rule = message.data["rule%s-rule" % idx]
                    json_data.add_data({"model" : model,
                                        "description" : description,
                                        "filename" : filename,
                                        "rule" : rule})
                    idx += 1
                except:
                    loop_again = False

        self.send_http_response_ok(json_data.get())


    def _rest_plugin_start_stop(self, command, host = None, plugin = None):
        """ Send start xpl message to manager
            Then, listen for a response
            @param host : host to which we send command
            @param plugin : name of plugin
        """
        if host == None:
            host = self.get_sanitized_hostname()

        self.log.debug("Plugin : ask for %s %s on %s " % (command, plugin, host))

        ### Send xpl message
        cmd_message = XplMessage()
        cmd_message.set_type("xpl-cmnd")
        cmd_message.set_schema("domogik.system")
        cmd_message.add_data({"command" : command})
        cmd_message.add_data({"host" : host})
        cmd_message.add_data({"plugin" : plugin})
        self.myxpl.send(cmd_message)

        ### Listen for response
        # get xpl message from queue
        try:
            self.log.debug("Plugin : wait for answer...")
            if command == "start":
                message = self._get_from_queue(self._queue_system_start, "xpl-trig", "domogik.system", filter_data = {"command" : "start", "plugin" : plugin})
            elif command == "stop":
                message = self._get_from_queue(self._queue_system_stop, "xpl-trig", "domogik.system", filter_data= {"command" : "stop", "plugin" : plugin})
        except Empty:
            json_data = JSonHelper("ERROR", 999, "No data or timeout on %s plugin %s" % (command, plugin))
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("plugin")
            self.send_http_response_ok(json_data.get())
            return

        self.log.debug("Plugin : message received : %s" % str(message))

        # an error happens
        if 'error' in message.data:
            error_msg = message.data['error']
            json_data = JSonHelper("ERROR", 999, error_msg)
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())


        # no error
        else:
            json_data = JSonHelper("OK")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())

    def _rest_plugin_enable_disable(self, command, host, plugin):
        """ Send enable/disable xpl message to manager
            Then, listen for a response
            @param host : host to which we send command
            @param plugin : name of plugin
        """
        self.log.debug("Plugin : ask for %s %s on %s " % (command, plugin, host))

        ### Send xpl message
        cmd_message = XplMessage()
        cmd_message.set_type("xpl-cmnd")
        cmd_message.set_schema("domogik.system")
        cmd_message.add_data({"command" : command})
        cmd_message.add_data({"host" : host})
        cmd_message.add_data({"plugin" : plugin})
        self.myxpl.send(cmd_message)

        ### Listen for response
        # get xpl message from queue
        try:
            self.log.debug("Plugin : wait for answer...")
            message = self._get_from_queue(self._queue_system_list, "xpl-trig", "domogik.system", filter_data = {"command" : command, "plugin" : plugin})
        except Empty:
            json_data = JSonHelper("ERROR", 999, "No data or timeout on %s plugin %s" % (command, plugin))
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("plugin")
            self.send_http_response_ok(json_data.get())
            return

        self.log.debug("Plugin : message received : %s" % str(message))

        # an error happens
        if 'error' in message.data:
            error_msg = message.data['error']
            json_data = JSonHelper("ERROR", 999, error_msg)
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())

        # no error
        else:
            json_data = JSonHelper("OK")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())




######
# /plugin/config/ processing
######

    def _rest_plugin_config_list(self, id = None, hostname = None, key = None):
        """ list device technology config
            @param id : name of module
            @param key : key of config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("config")
        if id == None:
            for plugin in self._db.list_all_plugin_config():
                json_data.add_data(plugin)
        elif key == None:
            for plugin in self._db.list_plugin_config(id, hostname):
                json_data.add_data(plugin)
        else:
            plugin = self._db.get_plugin_config(id, hostname, key)
            if plugin is not None:
                json_data.add_data(plugin)
        self.send_http_response_ok(json_data.get())



    def _rest_plugin_config_set(self):
        """ set device technology config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("config")
        try:
            plugin = self._db.set_plugin_config(self.get_parameters("id"), \
                                                self.get_parameters("hostname"), \
                                                self.get_parameters("key"), \
                                                self.get_parameters("value"))
            json_data.add_data(plugin)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_plugin_config_del(self, id, hostname):
        """ delete device technology config
            @param id : module name
            @param hostname : host
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("config")
        try:
            for plugin in self._db.del_plugin_config(id, hostname):
                json_data.add_data(plugin)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_plugin_config_del_key(self, id, hostname, key):
        """ delete device technology config
            @param id : module name
            @param hostname : host
            @param key : key to delete
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("config")
        try:
            plugin = self._db.del_plugin_config_key(id, hostname, key)
            if plugin is not None:
                json_data.add_data(plugin)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())





######
# /account processing
######

    def rest_account(self):
        """ REST account management
        """
        self.log.debug("Account action")

        # Check url length
        if len(self.rest_request) < 2:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        # parameters initialisation
        self.parameters = {}

        ### auth #####################################
        if self.rest_request[0] == "auth":
            if len(self.rest_request) == 3:
                self._rest_account_auth(self.rest_request[1], self.rest_request[2])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return
    
        ### user #####################################
        elif self.rest_request[0] == "user":

            ### list 
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_account_user_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_account_user_list(id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
    
            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_user_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_user_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### password
            elif self.rest_request[1] == "password":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_user_password()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_account_user_del(id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                      self.jsonp, self.jsonp_cb)

            ### others ###################################
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed", self.jsonp, self.jsonp_cb)
                return

        ### person ###################################
        elif self.rest_request[0] == "person":

            ### list #####################################
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_account_person_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_account_person_list(id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
    
            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_person_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_person_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_account_person_del(id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                      self.jsonp, self.jsonp_cb)

            ### others ###################################
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed", self.jsonp, self.jsonp_cb)
                return

        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return



    def _rest_account_user_list(self, id = None):
        """ list accounts
            @param id : id of account
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        if id == None:
            for account in self._db.list_user_accounts():
                json_data.add_data(account)
        else:
            account = self._db.get_user_account(id)
            if account is not None:
                json_data.add_data(account)
        self.send_http_response_ok(json_data.get())

        
    def _rest_account_auth(self, login, password):
        """ check authentification
            @param login : login
            @param password : password
        """
        self.log.info("Try to authenticate as %s" % login)
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        login_ok = self._db.authenticate(login, password)
        if login_ok == True:
            self.log.info("Authentication OK")
            json_data.set_ok(description = "Authentification granted")
            json_data.set_data_type("account")
            account = self._db.get_user_account_by_login(login)
            if account is not None:
                json_data.add_data(account)
        else:
            self.log.warning("Authentication refused")
            json_data.set_error(999, "Authentification refused")
        self.send_http_response_ok(json_data.get())


    def _rest_account_user_add(self):
        """ add user account
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        try:
            # create user and person
            if self.get_parameters("person_id") == None:
                account = self._db.add_user_account_with_person(self.get_parameters("login"), \
                                                    self.get_parameters("password"), \
                                                    self.get_parameters("first_name"), \
                                                    self.get_parameters("last_name"), \
                                                    self.to_date(self.get_parameters("birthday")), \
                                                    bool(self.get_parameters("is_admin")), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
            # create an user and attach it to a person
            else:
                account = self._db.add_user_account(self.get_parameters("login"), \
                                                    self.get_parameters("password"), \
                                                    self.get_parameters("person_id"), \
                                                    bool(self.get_parameters("is_admin")), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_user_update(self):
        """ update user account
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        try:
            # update account with person data
            if self.get_parameters("person_id") == None:
                account = self._db.update_user_account_with_person(self.get_parameters("id"), \
                                                    self.get_parameters("login"), \
                                                    self.get_parameters("first_name"), \
                                                    self.get_parameters("last_name"), \
                                                    self.get_parameters("birthday"), \
                                                    self.get_parameters("is_admin"), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
            # update and attach to a person
            else:
                account = self._db.update_user_account(self.get_parameters("id"), \
                                                    self.get_parameters("login"), \
                                                    self.get_parameters("person_id"), \
                                                    self.get_parameters("is_admin"), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_user_password(self):
        """ update user password
        """
        self.log.info("Try to change password for account id %s" % self.get_parameters("id"))
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        change_ok = self._db.change_password(self.get_parameters("id"), \
                                          self.get_parameters("old"), \
                                          self.get_parameters("new"))
        if change_ok == True:
            self.log.info("Password updated")
            json_data.set_ok(description = "Password updated")
            json_data.set_data_type("account")
            account = self._db.get_user_account(self.get_parameters("id"))
            if account is not None:
                json_data.add_data(account)
        else:
            self.log.warning("Password not updated : error")
            json_data.set_error(999, "Error in updating password")
        self.send_http_response_ok(json_data.get())



    def _rest_account_user_del(self, id):
        """ delete user account
            @param id : account id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        try:
            account = self._db.del_user_account(id)
            json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_list(self, id = None):
        """ list persons
            @param id : id of person
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        if id == None:
            for person in self._db.list_persons():
                json_data.add_data(person)
        else:
            person = self._db.get_person(id)
            if person is not None:
                json_data.add_data(person)
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_add(self):
        """ add person
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        try:
            person = self._db.add_person(self.get_parameters("first_name"), \
                                         self.get_parameters("last_name"), \
                                         self.to_date(self.get_parameters("birthday")))
            json_data.add_data(person)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_update(self):
        """ update person
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        try:
            person = self._db.update_person(self.get_parameters("id"), \
                                            self.get_parameters("first_name"), \
                                            self.get_parameters("last_name"), \
                                            self.to_date(self.get_parameters("birthday")))
            json_data.add_data(person)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_del(self, id):
        """ delete person
            @param id : person id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        try:
            person = self._db.del_person(id)
            json_data.add_data(person)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())








######
# /queeucontent processing
######

    def rest_queuecontent(self):
        """ Display a queue content
        """
        self.log.debug("Display queue content")
        
        # Check url length
        if len(self.rest_request) != 1:
            self.send_http_response_error(999, "Bad url", self.jsonp, self.jsonp_cb)
            return

        if self.rest_request[0] == "system_list":
            self.rest_queuecontent_display(self._queue_system_list)
        elif self.rest_request[0] == "system_detail":
            self.rest_queuecontent_display(self._queue_system_detail)
        elif self.rest_request[0] == "system_start":
            self.rest_queuecontent_display(self._queue_system_start)
        elif self.rest_request[0] == "system_stop":
            self.rest_queuecontent_display(self._queue_system_stop)
        elif self.rest_request[0] == "command":
            self.rest_queuecontent_display(self._queue_command)


    def rest_queuecontent_display(self, my_queue):
        """ Display a queue content
        """
        # Queue size
        queue_size = my_queue.qsize()

        # Queue elements
        queue_data = []
        if queue_size > 0:
            idx = 0
            while idx < queue_size:
                idx += 1
                # Queue content
                elt_time, elt_data = my_queue.get_nowait()
                my_queue.put((elt_time, elt_data))
                queue_data.append({"time" : time.ctime(elt_time), "content" : str(elt_data)})

        # Send result
        json_data = JSonHelper("OK")
        json_data.set_data_type("queue %s" % self.rest_request[0])
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.add_data(queue_data)
        self.send_http_response_ok(json_data.get())



######
# /testlongpol processing
######

    def rest_testlongpoll(self):
        """ REST function to test longpoll feature
        """
        self.log.debug("Testing long poll action")
        num = random.randint(1, 15)
        time.sleep(num)
        data = {"number" : num}
        json_data = JSonHelper("OK")
        json_data.set_data_type("longpoll")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.add_data(data)
        self.send_http_response_ok(json_data.get())






#####
# /helper processing
#####

    def rest_helper(self):
        """ REST helpers
        """
        print("Helper action")

        output = None
        json_data = JSonHelper("OK")
        json_data.set_data_type("helper")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        
        command = self.rest_request[0]
        if len(self.rest_request) <= 1 and command != "help":
            self.send_http_response_error(999, 
                                         "Bad command, no command given or missing first option", 
                                         self.jsonp, self.jsonp_cb)
            return


        # get helper lib path
        if self._package_path == None:
            helper_path = self._src_prefix
        else:
            helper_path = self._package_path
        helper_path += "/domogik_packages/xpl/helpers/"

        if command == "help":
            output = ["List of available helpers :"]
            for root, dirs, files in os.walk(helper_path):
                for fic in files:
                    if fic[-3:] == ".py" and fic[0:2] != "__":
                        output.append(" - %s" % fic[0:-3])
            output.append("Type 'foo help' to get help on foo helper")


        else:
            ### check is plugin is shut
            if self._check_component_is_running(command):
                self.send_http_response_error(999, 
                                             "Warning : plugin '%s' is currently running. Actually, helpers usage are not allowed while associated plugin is running : you should stop the plugin to use helper. In next versions, helpers will be implemented in a different way, so that they should be used while associated plugin is running" % command,
                                              self.jsonp, self.jsonp_cb)
                return

            ### load helper and create object
            try:
                #for importer, plgname, ispkg in pkgutil.iter_modules(package.__path__):
                #for importer, plgname, ispkg in pkgutil.iter_modules(self._package_path):
                for root, dirs, files in os.walk(helper_path):
                    for fic in files:
                        if fic[-3:] == ".py" and fic[0:2] != "__":
                            if fic[0:-3] == command:
                                helper = __import__('domogik_packages.xpl.helpers.%s' % command, fromlist="dummy")
                                try:
                                    helper_object = helper.MY_CLASS["cb"]()
                                    if len(self.rest_request) == 2:
                                        output = helper_object.command(self.rest_request[1])
                                    else:
                                        output = helper_object.command(self.rest_request[1], \
                                                               self.rest_request[2:])
                                except HelperError as err:
                                    self.send_http_response_error(999, 
                                                      "Error : %s" % err.value,
                                                      self.jsonp, self.jsonp_cb)
                                    return
                    
                        

            except:
                json_data.add_data(self.get_exception())
                self.send_http_response_ok(json_data.get())
                return

        if output != None:
            for line in output:
                json_data.add_data(line)
        else:
            json_data.add_data("<No result>")
        self.send_http_response_ok(json_data.get())




#####
# /repo processing
#####

    def rest_repo(self):
        """ REST repository : upload and download files
        """
        print("Repository action")

        ### put #####################################
        if self.rest_request[0] == "put":
            if self.command != "PUT":
                self.send_http_response_error(999, "HTTP %s command not allowed. Use PUT." % self.command, \
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_repo_put()

        ### get #####################################
        elif self.rest_request[0] == "get":
            if len(self.rest_request) != 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_repo_get(self.rest_request[1])
            
        ### others ##################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)


    def _rest_repo_put(self):
        """ Put a file on rest repository
        """
        status, data1, data2 = self._upload_file()
        if status:
            json_data = JSonHelper("OK")
            json_data.set_data_type("repository")
            json_data.add_data({"file" : data1})
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())
        else:
            self.send_http_response_error(999, data, self.jsonp, self.jsonp_cb)



    def _upload_file(self):
        """ Put a file on rest repository
            @Return : status (True/False), filename, file path
        """
        self.headers.getheader('Content-type')
        print(self.headers)
        content_length = int(self.headers['Content-Length'])

        if hasattr(self, "_put_filename") == False or self._put_filename == None:
            print("No file name given!!!")
            return False, "You must give a file name : ?filename=foo.txt", ""
        self.log.info("PUT : uploading %s" % self._put_filename)

        # TODO : check filename value (extension, etc)

        # replace name (without extension) with an unique id
        #basename, extension = os.path.splitext(self._put_filename)
        #file_id = str(uuid.uuid4())
        file_name = self._put_filename
        file_path = "%s/%s" % (self.repo_dir, file_name)

        try:
            up_file = open(file_path, "w")
            up_file.write(self.rfile.read(content_length))
            up_file.close()
        except IOError:
            self.log.error("PUT : failed to upload '%s' : %s" % (self._put_filename, traceback.format_exc()))
            print(traceback.format_exc())
            return False, "Error while writing '%s' : %s" % (file, traceback.format_exc()), ""

        self.log.info("PUT : uploaded as %s" % (file_path))
        return True, file_name, file_path


    def _rest_repo_get(self, file_name):
        """ Get a file from rest repository
        """
        # Check file opening
        self._download_file("%s/%s" % (self.repo_dir, file_name))


    ##### TEMPORARY FUNCTION THAT WILL NOT BE USED (AND DELETED)
    ##### IN NEXT RELEASES

    def _check_component_is_running(self, name, my_foo = None):
        ''' This method will send a ping request to a component
        and wait for the answer (max 5 seconds).
        @param name : component name
       
        Notice : sort of a copy of this function is used in rest.py to check 
                 if a plugin is on before using a helper
                 Helpers will change in future, so the other function should
                 disappear. There is no need for the moment to put this function
                 in a library
        '''
        self.log.info("Check if '%s' is running... (thread)" % name)
        self._pinglist[name] = Event()
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_target("xpl-%s.%s" % (name, self.get_sanitized_hostname()))
        mess.set_schema('hbeat.request')
        mess.add_data({'command' : 'request'})
        Listener(self._cb_check_component_is_running, 
                 self.myxpl, 
                 {'schema':'hbeat.app', 
                  'xpltype':'xpl-stat', 
                  'xplsource':"xpl-%s.%s" % (name, self.get_sanitized_hostname())},
                cb_params = {'name' : name})
        max = PING_DURATION
        while max != 0:
            self.myxpl.send(mess)
            time.sleep(1)
            max = max - 1
            if self._pinglist[name].isSet():
                break
        if self._pinglist[name].isSet():
            self.log.info("'%s' is running" % name)
            return True
        else:
            self.log.info("'%s' is not running" % name)
            return False


    def _cb_check_component_is_running(self, message, args):
        ''' Set the Event to true if an answer was received
        '''
        self._pinglist[args["name"]].set()

    ##### END OF TEMPORARY FUNCTIONS


#####
# /scenario processing
#####

    def rest_scenario(self):
        """ REST scenario 
        """
        print("Scenario action")

        ### list-templates #####################################
        if self.rest_request[0] == "list-templates":
            if len(self.rest_request) != 1:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_list_templates()

        ### detail-templates #####################################
        elif self.rest_request[0] == "detail-templates":
            if len(self.rest_request) != 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_detail_templates(self.rest_request[1])

        ### list-instances #####################################
        elif self.rest_request[0] == "list-instances":
            if len(self.rest_request) != 1:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_list_instances()
            
        ### detail-instances #####################################
        elif self.rest_request[0] == "detail-instances":
            if len(self.rest_request) != 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_detail_instances(self.rest_request[1])
            
        ### add #####################################
        elif self.rest_request[0] == "add":
            offset = 2
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_add()

        ### update #####################################
        elif self.rest_request[0] == "update":
            offset = 2
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_update()
            
        ### del #####################################
        elif self.rest_request[0] == "del":
            if len(self.rest_request) != 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_del(self.rest_request[1])
            
        ### start #####################################
        elif self.rest_request[0] == "start":
            if len(self.rest_request) != 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_start(self.rest_request[1])
            
        ### stop #####################################
        elif self.rest_request[0] == "stop":
            if len(self.rest_request) != 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_scenario_stop(self.rest_request[1])
            
        ### others ##################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)


######
# /package processing
######

    def rest_package(self):
        """ /package processing
        """
        self.log.debug("Package action")

        # parameters initialisation
        self.parameters = {}

        if len(self.rest_request) < 1:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### get-mode ##################################
        if self.rest_request[0] == "get-mode":

            if len(self.rest_request) == 1:
                self._rest_package_get_mode()
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### list-repo #################################
        elif self.rest_request[0] == "list-repo":

            if len(self.rest_request) == 1:
                self._rest_package_list_repo()
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### update-cache #############################
        elif self.rest_request[0] == "update-cache":
            if len(self.rest_request) == 1:
                self._rest_package_update_cache()
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### icon #####################################
        elif self.rest_request[0] == "icon":
            if self.rest_request[1] == "available":
                if len(self.rest_request) == 5:
                    self._rest_package_icon_available(self.rest_request[2],
                                                      self.rest_request[3],
                                                      self.rest_request[4])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                    return
            elif self.rest_request[1] == "installed":
                if len(self.rest_request) == 4:
                    self._rest_package_icon_installed(self.rest_request[2],
                                                      self.rest_request[3])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                    return
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### available ################################
        elif self.rest_request[0] == "available":
            if len(self.rest_request) == 3:
                self._rest_package_available(self.rest_request[1],
                                             self.rest_request[2])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### installed ################################
        elif self.rest_request[0] == "installed":
            if len(self.rest_request) == 3:
                self._rest_package_installed(self.rest_request[1],
                                                  self.rest_request[2])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### dependency ###############################
        elif self.rest_request[0] == "dependency":
            if len(self.rest_request) == 5:
                self._rest_package_dependency(self.rest_request[1],
                                           self.rest_request[2],
                                           self.rest_request[3],
                                           self.rest_request[4])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### install ##################################
        elif self.rest_request[0] == "install":
            if len(self.rest_request) == 5:
                self._rest_package_install(self.rest_request[1],
                                           self.rest_request[2],
                                           self.rest_request[3],
                                           self.rest_request[4])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### install_from_path ########################
        elif self.rest_request[0] == "install_from_path":
            if len(self.rest_request) == 2:
                self._rest_package_install_from_path(self.rest_request[1])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### uninstall ##################################
        elif self.rest_request[0] == "uninstall":
            if len(self.rest_request) == 4:
                self._rest_package_uninstall(self.rest_request[1],
                                             self.rest_request[2],
                                             self.rest_request[3])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### download #################################
        elif self.rest_request[0] == "download":
            if len(self.rest_request) == 4:
                self._rest_package_download(self.rest_request[1],
                                           self.rest_request[2],
                                           self.rest_request[3])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return

        ### others ####################################
        else:
            self.send_http_response_error(999, "Bad operation for /package", self.jsonp, self.jsonp_cb)
            return

    def _rest_package_get_mode(self):
        """ Get mode (devlopement of install) for packages management
        """
        self.log.debug("Package : ask for mode")

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("mode")
        if self._package_path == None:
            json_data.add_data("development")
        else:
            json_data.add_data("normal")
    
        self.send_http_response_ok(json_data.get())

    def _rest_package_list_repo(self):
        """ Get repositories list
            Display this list as json
        """
        self.log.debug("Package : ask for repositories list")

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("repository")

        pkg_mgr = PackageManager()
        try:
            for repo in pkg_mgr.get_repositories_list():
                json_data.add_data({"url" : repo['url'],
                               "priority" : repo['priority']})
        except PackageException:
            self.send_http_response_error(999, "Error while listing repositories : check rest.log file",
                                          self.jsonp, self.jsonp_cb)
            return
    
        self.send_http_response_ok(json_data.get())

    def _rest_package_update_cache(self):
        """ Update cache
        """
        self.log.debug("Package : ask for updating cache")

        self.pkg_mgr = PackageManager()
        if self.pkg_mgr.update_cache() == False:
            self.send_http_response_error(999, "Error while updating cache",
                                          self.jsonp, self.jsonp_cb)
        else:
            self._get_installed_packages_from_manager()
            json_data = JSonHelper("OK")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("cache")
            self.send_http_response_ok(json_data.get())

    def _rest_package_available(self, host, pkg_type):
        """ Get packages list not already installed
            Display this list as json
            @param host : filter on host
            @param pkg_type : filter on package type
        """
        self.log.debug("Package : ask for available packages list")

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("package")

        list_installed = []
        pkg_list = self.get_installed_packages()
        if pkg_list.has_key(host):
            if pkg_list[host].has_key(pkg_type):
                for elt in pkg_list[host][pkg_type]:
                    list_installed.append(elt["id"])

        pkg_mgr = PackageManager()
        pkg_list = []
        # get package list for the type
        for data in pkg_mgr.get_packages_list(pkg_type = pkg_type):
            if data["id"] not in list_installed:
                json_data.add_data(data)

        self.send_http_response_ok(json_data.get())


    def _rest_package_installed(self, host, pkg_type):
        """ Send a xpl message to manager to get installed packages list
            Display this list as json
            @param host : host
            @param pkg_type : type of package
        """
        self.log.debug("Package : ask for installed packages list")
       
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("package")
        pkg_list = self.get_installed_packages()
        if pkg_list.has_key(host):
            if pkg_list[host].has_key(pkg_type):
                for elt in pkg_list[host][pkg_type]:
                    json_data.add_data(elt)
        self.send_http_response_ok(json_data.get())

    #def _rest_package_send_xpl_to_get_installed_list(self, host, pkg_type):
    #    """ Send a xpl message to manager to get installed packages list
    #        @param host : host
    #        @param pkg_type : type of package
    #    """

    #    ### Send xpl message to get list
    #    message = XplMessage()
    #    message.set_type("xpl-cmnd")
    #    message.set_schema("domogik.package")
    #    message.add_data({"command" : "installed-packages-list"})
    #    message.add_data({"host" : host})
    #    self.myxpl.send(message)

    #    ### Wait for answer
    #    # get xpl message from queue
    #    # make a time loop of one second after first xpl-trig reception
    #    messages = []
    #    try:
    #        # Get answer for command
    #        self.log.debug("Package repository list : wait for first answer...")
    #        message = self._get_from_queue(self._queue_package, 
    #                                             "xpl-trig", 
    #                                             "domogik.package",
    #                                             filter_data = {"command" : "installed-packages-list"})
    #    except Empty:
    #        self.log.debug("Installed packages list : no answer")
    #        return False, "No data or timeout on getting installed packages list"
    #    return True, message


    def _rest_package_dependency(self, host, pkg_type, id, version):
        """ Send a xpl message to check python dependencies
            @param host : host targetted
            @param pkg_type : type of package
            @param id ; id of package
            @param version : package version
            Return status of each dependency as json
        """
        self.log.debug("Package : ask for checking dependencies for a package")
        package = "%s-%s" % (pkg_type, id)

        ### check package exists in cache
        pkg_mgr = PackageManager()
        data = pkg_mgr.get_packages_list(fullname = package, version = version)
        print data
        # if there is no package corresponding
        if data == []:
            self.log.debug("No package corresponding to check dependency request")
            self.send_http_response_error(999, "No package corresponding to request",
                                          self.jsonp, self.jsonp_cb)
            return
        self._rest_get_dependency(host, pkg_type, data[0]["dependencies"])

    def _rest_get_dependency(self, host, pkg_type, dep_list):
        """ Send a xpl message to check the package dependencies
            return a json
            @param host : host
            @param pkg_type : package type
            @param dep_list : list of dependencies [{"type": , "id": }, {}...]
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("dependency")

        ### list dependencies
        idx_python = 0
        idx_plugin = 0
        python_dep = []
        pkg_mgr = PackageManager()
        pkg_list = self.get_installed_packages()
        for dep in dep_list:
            if dep["type"] == "python":
                python_dep.append({"dep%s" % idx_python : dep["id"]})
                idx_python += 1

            if dep["type"] == "plugin":
                id = dep["id"].split(" ")[0]
                installed = False

                if pkg_list.has_key(host):
                    if pkg_list[host].has_key(pkg_type):
                        for elt in pkg_list[host][pkg_type]:
                            if elt["id"] == id:
                                installed = True

                data = {
                           "type" : "plugin",
                           "id" : dep["id"],
                           "installed" : installed,
                           "version" : "",
                           "cmd_line" : "Install from Domogik Administration",
                           "candidate" : "",
                           "error" : "",
                           }
                json_data.add_data(data)
                idx_plugin += 1

        ### check python dependencies
        # if there are python dependencies, ask on xpl
        if idx_python != 0:
            ### Send xpl message to check python dependencies on host
            message = XplMessage()
            message.set_type("xpl-cmnd")
            message.set_schema("domogik.package")
            message.add_data({"command" : "check-dependencies"})
            message.add_data({"host" : host})
            for the_dep in python_dep:
                message.add_data(the_dep)
            self.myxpl.send(message)

            ### Wait for answer
            # get xpl message from queue
            # make a time loop of one second after first xpl-trig reception
            messages = []
            try:
                self.log.debug("Package check dependencies : wait for answer...")
                message = self._get_from_queue(self._queue_package, 
                                               "xpl-trig", 
                                               "domogik.package", 
                                               filter_data = {"command" : "check-dependencies", "host" : host},
                                               timeout = WAIT_FOR_DEPENDENCY_CHECK)
            except Empty:
                self.log.debug("Package dependencies check : no answer")
                self.send_http_response_error(999, "No data or timeout on checking dependencies",
                                              self.jsonp, self.jsonp_cb)
                return
    
            self.log.debug("Package dependencies check : message receive : %s" % str(message))
            
            # process message
            if message.data.has_key('error'):
                self.send_http_response_error(999, "Error : %s" % message.data['error'], self.jsonp, self.jsonp_cb)
                return
            else:
                idx = 0
                loop_again = True
                dep_list = []
                while loop_again:
                    try:
                        my_key = message.data["dep%s" % idx]
                        if message.data["dep%s-installed" % idx].lower() == "yes":
                            installed = True
                        else:
                            installed = False
                        if message.data.has_key("dep%s-version" % idx):
                            version = message.data["dep%s-version" % idx]
                        else:
                            version = ""
                        if message.data.has_key("dep%s-cmd-line" % idx):
                            cmd_line = message.data["dep%s-cmd-line" % idx]
                        else:
                            cmd_line = ""
                        if message.data.has_key("dep%s-candidate" % idx):
                            candidate = message.data["dep%s-candidate" % idx]
                        else:
                            candidate = ""
                        if message.data.has_key("dep%s-error" % idx):
                            error = message.data["dep%s-error" % idx]
                        else:
                            error = ""
        
                        data = {
                                   "type" : "python",
                                   "id" : my_key,
                                   "installed" : installed,
                                   "version" : version,
                                   "cmd_line" : cmd_line,
                                   "candidate" : candidate,
                                   "error" : error,
                               }
                        json_data.add_data(data)
                        idx += 1
                    except:
                        loop_again = False
        self.send_http_response_ok(json_data.get())

    def _rest_package_install(self, host, type, id, version):
        """ Send xpl messages to install a package :
            - one to manager on target host for "bin" files
            - one to manager on rinor's host for rest's xml files
            @param host : host targetted
            @param type : type of package
            @param id : id of package
            @param version : package version
            Return ok/ko as json
        """
        self.log.debug("Package : ask for installing a package")
        package = "%s/%s/%s" % (type, id, version)

        pkg_mgr = PackageManager()
        res = pkg_mgr.cache_package(PKG_CACHE_DIR, type, id, version)
        # if package not cachable (doesn't exists, ...)
        if res == False:
            self.send_http_response_error(999, "Error on putting package in cache", self.jsonp, self.jsonp_cb)

        #### Send xpl message to install package's rinor part
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.package")
        message.add_data({"command" : "install"})
        message.add_data({"host" : self.get_sanitized_hostname()})
        message.add_data({"source" : "cache"})
        message.add_data({"type" : type})
        message.add_data({"id" : id})
        message.add_data({"version" : version})
        message.add_data({"part" : PKG_PART_RINOR})
        self.myxpl.send(message)
        
        ### Wait for answer
        # get xpl message from queue
        messages = []
        try:
            self.log.debug("Package install : wait for answer...")
            message = self._get_from_queue(self._queue_package, 
                                           "xpl-trig", 
                                           "domogik.package", 
                                           filter_data = {"command" : "install",
                                                          "source" : "cache",
                                                          "type" : type,
                                                          "id" : id,
                                                          "version" : version,
                                                         "host" : self.get_sanitized_hostname()},
                                           timeout = WAIT_FOR_PACKAGE_INSTALLATION)
        except Empty:
            self.log.debug("Package install : no answer")
            self.send_http_response_error(999, "No data or timeout on installing package",
                                          self.jsonp, self.jsonp_cb)
            return
        
        self.log.debug("Package install : message received for '%s' part : %s" % (PKG_PART_RINOR, str(message)))
        
        # process message
        if message.data.has_key('error'):
            self.send_http_response_error(999, "Error on '%s' part : %s" % (PKG_PART_RINOR, message.data['error']), self.jsonp, self.jsonp_cb)


        ### Send xpl message to install package bin part
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.package")
        message.add_data({"command" : "install"})
        message.add_data({"host" : host})
        message.add_data({"source" : "cache"})
        message.add_data({"type" : type})
        message.add_data({"id" : id})
        message.add_data({"version" : version})
        message.add_data({"part" : PKG_PART_XPL})
        self.myxpl.send(message)

        ### Wait for answer
        # get xpl message from queue
        messages = []
        try:
            self.log.debug("Package install : wait for answer...")
            message = self._get_from_queue(self._queue_package, 
                                           "xpl-trig", 
                                           "domogik.package", 
                                           filter_data = {"command" : "install",
                                                          "source" : "cache",
                                                          "type" : type,
                                                          "id" : id,
                                                          "version" : version,
                                                          "host" : host},
                                           timeout = WAIT_FOR_PACKAGE_INSTALLATION)
        except Empty:
            self.log.debug("Package install : no answer")
            self.send_http_response_error(999, "No data or timeout on installing package",
                                          self.jsonp, self.jsonp_cb)
            return

        self.log.debug("Package install : message received for '%s' part : %s" % (PKG_PART_XPL, str(message)))
        

        # process message
        if message.data.has_key('error'):
            self.send_http_response_error(999, "Error on '%s' part : %s" % (PKG_PART_XPL, message.data['error']), self.jsonp, self.jsonp_cb)
            return


        else:
            json_data = JSonHelper("OK")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("install")
            self.send_http_response_ok(json_data.get())

    def _rest_package_install_from_path(self, host):
        """ Upload a local package file (from UI host) and install it
            @param host : host targetted
            Return ok/ko as json
        """
        self.log.debug("Package : ask for installing an uploaded package")

        #### upload the file
        status, data1, data2 = self._upload_file()
        if not status:
            self.send_http_response_error(999, data1, self.jsonp, self.jsonp_cb)
            return
        print data1
        #json_data = JSonHelper("OK")
        #json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        #json_data.set_data_type("install_from_path")
        #self.send_http_response_ok(json_data.get())

        if data1[-4:] != ".tgz":
            self.send_http_response_error(999, "Bad filename provided. It must be a .tgz file", self.jsonp, self.jsonp_cb)
            return
        try:
            buf = data1[:-4].split("-")
            pkg_type = buf[0]
            pkg_id = buf[1]
            pkg_version = buf[2]
            package = "%s/%s/%s" % (pkg_type, pkg_id, pkg_version)
        except:
            self.send_http_response_error(999, "Bad filename provided.", self.jsonp, self.jsonp_cb)
            return

        print package

        pkg_mgr = PackageManager()
        res = pkg_mgr.cache_package(PKG_CACHE_DIR, pkg_type, pkg_id, pkg_version, data2)
        # if package not cachable (doesn't exists, ...)
        if res == False:
            self.send_http_response_error(999, "Error on putting package in cache", self.jsonp, self.jsonp_cb)

        #### Send xpl message to install package's rinor part
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.package")
        message.add_data({"command" : "install"})
        message.add_data({"host" : self.get_sanitized_hostname()})
        message.add_data({"source" : "cache"})
        message.add_data({"type" : pkg_type})
        message.add_data({"id" : pkg_id})
        message.add_data({"version" : pkg_version})
        message.add_data({"part" : PKG_PART_RINOR})
        self.myxpl.send(message)
        
        ### Wait for answer
        # get xpl message from queue
        messages = []
        try:
            self.log.debug("Package install : wait for answer...")
            message = self._get_from_queue(self._queue_package, 
                                           "xpl-trig", 
                                           "domogik.package", 
                                           filter_data = {"command" : "install",
                                                          "source" : "cache",
                                                          "type" : pkg_type,
                                                          "id" : pkg_id,
                                                          "version" : pkg_version,
                                                         "host" : self.get_sanitized_hostname()},
                                           timeout = WAIT_FOR_PACKAGE_INSTALLATION)
        except Empty:
            self.log.debug("Package install : no answer")
            self.send_http_response_error(999, "No data or timeout on installing package",
                                          self.jsonp, self.jsonp_cb)
            return
        
        self.log.debug("Package install : message received for '%s' part : %s" % (PKG_PART_RINOR, str(message)))
        
        # process message
        if message.data.has_key('error'):
            self.send_http_response_error(999, "Error on '%s' part : %s" % (PKG_PART_RINOR, message.data['error']), self.jsonp, self.jsonp_cb)


        ### Send xpl message to install package bin part
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.package")
        message.add_data({"command" : "install"})
        message.add_data({"host" : host})
        message.add_data({"source" : "cache"})
        message.add_data({"type" : pkg_type})
        message.add_data({"id" : pkg_id})
        message.add_data({"version" : pkg_version})
        message.add_data({"part" : PKG_PART_XPL})
        self.myxpl.send(message)

        ### Wait for answer
        # get xpl message from queue
        messages = []
        try:
            self.log.debug("Package install : wait for answer...")
            message = self._get_from_queue(self._queue_package, 
                                           "xpl-trig", 
                                           "domogik.package", 
                                           filter_data = {"command" : "install",
                                                          "source" : "cache",
                                                          "type" : pkg_type,
                                                          "id" : pkg_id,
                                                          "version" : pkg_version,
                                                          "host" : host},
                                           timeout = WAIT_FOR_PACKAGE_INSTALLATION)
        except Empty:
            self.log.debug("Package install : no answer")
            self.send_http_response_error(999, "No data or timeout on installing package",
                                          self.jsonp, self.jsonp_cb)
            return

        self.log.debug("Package install : message received for '%s' part : %s" % (PKG_PART_XPL, str(message)))
        

        # process message
        if message.data.has_key('error'):
            self.send_http_response_error(999, "Error on '%s' part : %s" % (PKG_PART_XPL, message.data['error']), self.jsonp, self.jsonp_cb)
            return


        else:
            json_data = JSonHelper("OK")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("install")
            self.send_http_response_ok(json_data.get())

    def _rest_package_uninstall(self, host, type, id):
        """ Send xpl messages to install a package :
            - one to manager on target host for "bin" files
            - one to manager on rinor's host for rest's xml files
            @param host : host targetted
            @param type : package type
            @param id : package id
            Return ok/ko as json
        """
        self.log.debug("Package : ask for uninstalling a package")
        package = "%s-%s" % (type, id)

        ### Send xpl message to uninstall package
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.package")
        message.add_data({"command" : "uninstall"})
        message.add_data({"host" : host})
        message.add_data({"type" : type})
        message.add_data({"id" : id})
        self.myxpl.send(message)

        ### Wait for answer
        # get xpl message from queue
        messages = []
        try:
            self.log.debug("Package uninstall : wait for answer...")
            message = self._get_from_queue(self._queue_package, 
                                           "xpl-trig", 
                                           "domogik.package", 
                                           filter_data = {"command" : "uninstall",
                                                          "type" : type,
                                                          "id" : id,
                                                          "host" : host},
                                           timeout = WAIT_FOR_PACKAGE_INSTALLATION)
        except Empty:
            self.log.debug("Package uninstall : no answer")
            self.send_http_response_error(999, "No data or timeout on uninstalling package",
                                          self.jsonp, self.jsonp_cb)
            return

        self.log.debug("Package uninstall : message received : %s" % (str(message)))
        

        # process message
        if message.data.has_key('error'):
            self.send_http_response_error(999, "Error : %s" % (message.data['error']), self.jsonp, self.jsonp_cb)
            return
        else:
            json_data = JSonHelper("OK")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("uninstall")
            self.send_http_response_ok(json_data.get())


    def _rest_package_icon_available(self, type, id, version):
        """ Download a package icon storen in cache
        """
        icon_name = "icon_%s_%s_%s.png" % (type, id, version)
        file_name = "%s/%s" % (ICON_CACHE_DIR, icon_name)
        self._download_file(file_name)


    def _rest_package_icon_installed(self, type, id):
        """ Download a package icon storen in cache
        """
        file_name = "%s/%s/%s/icon.png" % (self._design_dir, type, id)
        self._download_file(file_name)


    def _rest_package_download(self, type, id, version):
        """ Download a package storen in cache
        """
        pkg_path = "%s-%s-%s.tgz" % (type, id, version)
        file_name = "%s/%s" % (PKG_CACHE_DIR, pkg_path)
        self._download_file(file_name)



######
# /log processing
######

    def rest_log(self):
        """ /log processing
        """
        self.log.debug("Log action")

        # parameters initialisation
        self.parameters = {}

        if len(self.rest_request) < 1:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### tail ######################################
        if self.rest_request[0] == "tail":
    
            ### txt #######################################
            if self.rest_request[1] == "txt":
    
                if len(self.rest_request) == 6:
                    self._rest_log_tail_txt(self.rest_request[2],
                                            self.rest_request[3],
                                            self.rest_request[4],
                                            self.rest_request[5])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                    return
    
            ### html ######################################
            if self.rest_request[1] == "html":
    
                if len(self.rest_request) == 6:
                    self._rest_log_tail_html(self.rest_request[2],
                                             self.rest_request[3],
                                             self.rest_request[4],
                                             self.rest_request[5])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                    return
    
            ### others ####################################
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
                return
    
        ### others ####################################
        else:
            self.send_http_response_error(999, "Bad operation for /log", self.jsonp, self.jsonp_cb)
            return

    def _rest_log_tail_txt(self, host, filename, number, offset):
        """ Send (raw format!!) result of a tail
            @param host : hostname for file
            @param filename : filename (without ".log")
            @param number : number of lines
            @param offset : offset in lines from end of file
        """
        self.log.debug("Log : ask for tail action : %s > %s" % (host, filename))

        if host == self.get_sanitized_hostname():
            subdir = ""
        else:
            subdir = host.lower()
        path = "%s/%s/%s.log" % (self.log_dir_path, subdir, os.path.basename(filename))
        try:
            result = Tail(path, int(number), int(offset)).get()
        except IOError:
            result = "Unable to read '%s' file" % path
        self.send_http_response_text_plain(result)

    def _rest_log_tail_html(self, host, filename, number, offset):
        """ Send (html format!!) result of a tail
            @param host : hostname for file
            @param filename : filename (without ".log")
            @param number : number of lines
            @param offset : offset in lines from end of file
        """
        self.log.debug("Log : ask for tail action : %s > %s" % (host, filename))

        if host == self.get_sanitized_hostname():
            subdir = ""
        else:
            subdir = host.lower()
        path = "%s/%s/%s.log" % (self.log_dir_path, subdir, os.path.basename(filename))
        try:
            result = Tail(path, int(number), int(offset)).get_html()
        except IOError:
            result = "Unable to read '%s' file" % path
        self.send_http_response_text_html(result)

######
# /host processing
######

    def rest_host(self):
        """ /host processing
        """
        self.log.debug("Host action")

        # parameters initialisation
        self.parameters = {}

        ### list hosts ############################
        if len(self.rest_request) == 0:
            self._rest_host_list()

        ### detail for a host #####################
        elif len(self.rest_request) == 1:
            self._rest_host_list(self.rest_request[0])

        ### others ####################################
        else:
            self.send_http_response_error(999, "Bad operation for /host", self.jsonp, self.jsonp_cb)
            return

    def _rest_host_list(self, host = None):
        """ Get hosts list
            Display this list as json
        """
        self.log.debug("Host : ask for list")

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("host")

        if host == None:
            for my_host in self._hosts_list:
                json_data.add_data({"id" : my_host,
                                    "primary" : self._hosts_list[my_host]["primary"]})
        else:
            try:
                json_data.add_data(self._hosts_list[host])
            except KeyError:
                json_data.add_data({})
        self.send_http_response_ok(json_data.get())


##########
# Tools
##########

    def _download_file(self, file_name):
        """ Download a file
        """
        # Check file opening
        try:
            my_file = open("%s" % (file_name), "rb")
        except IOError:
            self.send_http_response_404()
            return

        # Get informations on file
        ctype = None
        file_stat = os.fstat(my_file.fileno())
        #last_modified = os.stat("%s" % (file_name))[stat.ST_MTIME]
        last_modified = os.path.getmtime(file_name)

        # Get mimetype information
        if not mimetypes.inited:
            mimetypes.init()
        extension_map = mimetypes.types_map.copy()
        extension_map.update({
                '' : 'application/octet-stream', # default
                '.py' : 'text/plain'})
        basename, extension = os.path.splitext(file_name)
        if extension in extension_map:
            ctype = extension_map[extension] 
        else:
            extension = extension.lower()
            if extension in extension_map:
                ctype = extension_map[extension] 
            else:
                ctype = extension_map[''] 

        # Send file
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(file_stat[6]))
        self.send_header("Last-Modified", last_modified)
        self.end_headers()
        shutil.copyfileobj(my_file, self.wfile)
        my_file.close()

