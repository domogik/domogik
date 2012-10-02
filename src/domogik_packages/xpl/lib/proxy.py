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

Proxy library

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import traceback
from hashlib import md5
import base64
from time import time, strftime
from random import randint
from domogik.xpl.common.xplmessage import XplMessage
#import XyneHTTPServer
#import BaseHTTPServer, select, socket, SocketServer, urlparse
import BaseHTTPServer
from domogik.common.database import DbHelper, DbHelperException
#from domogik_packages.xpl.lib.XyneHTTPServer import BaseHTTPRequestHandler
import SocketServer, urlparse, socket, select

class ProxyException(Exception):
    """
    proxy exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

class ProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    Proxy Handler
    """
    __base = BaseHTTPServer.BaseHTTPRequestHandler

    __base_handle = __base.handle

    __version__ = "0.1"

    server_version = "RestProxy/" + __version__

    #rbufsize = 8192                        # self.rfile Be unbuffered
    rbufsize = 16384

    realm = "Domogik"

    both_current = 0

    ##### HTTP Authentication #####

    # nc limit: maximum value is 0xffffffff
    # The client must re-auth after this number of requests.
    NC_LIMIT = 0xffffffff

    # Client must re-auth if no requests were made in the last x seconds
    OPAQUE_TIMEOUT = 3600

    # nonce and opaque lengths
    NONCE_LENGTH = 32

    # Opaque values
    opaques = {}

    ##### Meta #####

    # HTTP protocol version
    protocol_version = 'HTTP/1.1'

    # Server version.
    def version_string(self):
        """
        """
        return self.server_version

    # Create a nonce value
    def create_nonce(self):
        """
        """
        NONCE_MAX = 2 ** (self.NONCE_LENGTH * 4) - 1
        NONCE_FORMAT = '%0' + str(self.NONCE_LENGTH) + 'x'
        return NONCE_FORMAT % randint(0, NONCE_MAX)

    # Get the nonce value
    def get_nonce(self,opaque,nc):
        """
        """
        # Purge values that have timed out or exceeded the limit
        t = time()
        for k in self.opaques.keys():
            if t - self.opaques[k]['time'] > self.OPAQUE_TIMEOUT or int(self.opaques[k]['nc'],16) > self.NC_LIMIT:
                del self.opaques[k]
        try:
            if self.opaques[opaque]['nc'] != nc:
                del self.opaques[opaque]
                return ''
            self.opaques[opaque]['nc'] = "%08x" % (int(nc,16) + 1)
            self.opaques[opaque]['time'] = t
            return self.opaques[opaque]['nonce']
        except KeyError:
            return None

    # Reject an unauthenticated request.
    def reject_unauthenticated_request(self):
        """
        """
        if self.server.auth_method == "basic" or \
          (self.server.auth_method == "both" and self.both_current == 1) :
            self.send_response(401)
            self.send_header('Content-Length', 0)
            self.send_header('WWW-Authenticate', 'Basic realm="' + self.realm + '"')
            self.send_header('Connection', 'close')
            self.end_headers()
        elif self.server.auth_method == "digest" or \
          (self.server.auth_method == "both" and self.both_current == 0):
            nonce =  self.create_nonce()
            opaque = self.create_nonce()
            self.opaques[opaque] = {'time': time(), 'nc': '00000001', 'nonce': nonce}
            self.send_response(401)
            self.send_header('Content-Length', 0)
            self.send_header('WWW-Authenticate', 'Digest realm="' + self.realm + '",qop="auth",nonce="' + nonce +'",opaque="' + opaque +'"')
            self.send_header('Connection', 'close')
            self.end_headers()

    def authenticate(self, method='GET'):
        """
        Check authentification using the defined method in server
        """
        if self.server.auth_method == "none" :
            self.server.log.debug("Authenticate %s using method none" % self.address_string())
            return True
        elif self.server.auth_method == "basic" :
            return self.basic_auth(method)
        elif self.server.auth_method == "digest" :
            return self.digest_auth(method)
        elif self.server.auth_method == "both" :
            self.both_current == 0
            ret = self.digest_auth(method)
            if not ret :
                self.both_current == 1
                ret = self.basic_auth(method)
            return ret
        self.server.log.error("Unknow authentication method %s" % self.server.auth_method)
        return False

    def basic_auth(self, method='GET'):
        """
        Basic authentification
        @param method : http method
        """
        username = self.server.username
        password = self.server.password
        if username and password :
            if 'Authorization' in self.headers and self.headers['Authorization'][:6] == 'Basic ':

                base64_valid = base64.encodestring('%s:%s' % (username, password))[:-1]
                #print "base64_valid %s" % base64_valid
                # Parse given Authorization
                try:
                    base64_user_raw = self.headers.getfirstmatchingheader('authorization').pop().strip()
                    base64_user = base64_user_raw.split('Basic ')[1]
                except:
                    base64_user = ''

                if base64_user==base64_valid:
                    self.server.log.debug("Authenticate %s using method basic" % self.address_string())
                    return True

            #print "self.headers['Authorization'] %s" % self.headers['Authorization']
            self.reject_unauthenticated_request()
            return False
        else:
            self.reject_unauthenticated_request()
            return False
        return False

    def digest_auth(self, method='GET'):
        """
        Digest authentification
        @param method : http method
        """
        username = self.server.username
        password = self.server.password
        if username and password:
            if 'Authorization' in self.headers and self.headers['Authorization'][:7] == 'Digest ':
                nc = None
                cnonce = None
                opaque = None
                client_response = None
                for field in self.headers['Authorization'][7:].split(','):
                    field = field.strip()
                    if field[:10] == 'response="':
                        client_response = field[10:-1]
                    elif field[:8] == 'cnonce="':
                        cnonce = field[8:-1]
                    elif field[:3] == 'nc=':
                        nc = field[3:]
                    elif field[:8] == 'opaque="':
                        opaque = field[8:-1]
                if client_response != None and cnonce != None and opaque != None and nc != None:
                    nonce = self.get_nonce(opaque,nc)
                    if not nonce:
                        self.reject_unauthenticated_request()
                        return False
                    m = md5()
                    m.update(username + ':' + self.realm + ':' + password)
                    ha1 = m.hexdigest()
                    m = md5()
                    m.update(method + ':' + self.path)
                    ha2 = m.hexdigest()
                    m = md5()
                    m.update(ha1 + ':' + nonce + ':' + nc + ':' + cnonce + ':auth:' + ha2)
                    response = m.hexdigest()
                    if response == client_response:
                        self.server.log.debug("Authenticate %s using method digest" % self.address_string())
                        return True
            self.reject_unauthenticated_request()
            return False
        else:
            self.reject_unauthenticated_request()
            return False

    def _connect_to(self, netloc, soc):
        """
        @param netloc : http address
        @param soc : socket to use
        """
        i = netloc.find(':')
        if i >= 0:
            host_port = netloc[:i], int(netloc[i+1:])
        else:
            host_port = netloc, 80
        #print "\t" "connect to %s:%d" % host_port
        self.server.log.debug("Connect to %s:%d" % host_port)
        try:
            soc.connect(host_port)
        except socket.error, arg:
            try:
                msg = arg[1]
            except:
                msg = arg
            self.send_error(404, msg)
            return 0
        return 1

    def do_authenticated_CONNECT(self):
        """
        """
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if self._connect_to(self.path, soc):
                self.log_request(200)
                self.wfile.write(self.protocol_version +
                                 " 200 Connection established\r\n")
                self.wfile.write("Proxy-agent: %s\r\n" % self.version_string())
                self.wfile.write("\r\n")
                self._read_write(soc, 300)
        finally:
            #print "\t" "bye"
            soc.close()
            self.connection.close()

    def do_authenticated_GET(self):
        """
        """
        (scm, netloc, path, params, query, fragment) = urlparse.urlparse(
            self.path, 'http')
        netloc = "%s:%s" % (self.server.server[0], self.server.server[1])
        if scm != 'http' or fragment or not netloc:
            self.send_error(400, "bad url %s" % self.path)
            return
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if self._connect_to(netloc, soc):
                self.server.log.debug("Retrieve page %s" % (path))
                self.log_request()
                soc.send("%s %s %s\r\n" % (
                    self.command,
                    urlparse.urlunparse(('', '', path, params, query, '')),
                    self.request_version))
                self.headers['Connection'] = 'close'
                del self.headers['Proxy-Connection']
                for key_val in self.headers.items():
                    soc.send("%s: %s\r\n" % key_val)
                soc.send("\r\n")
                self._read_write(soc)
        finally:
            #print "\t" "bye"
            soc.close()
            self.connection.close()

    def _read_write(self, soc, max_idling=60):
        """
        @param soc : socket to use
        @param max_idling : counter to stop the connection
        """
        #print "_read_write %s" % soc
        iw = [self.connection, soc]
        ow = []
        count = 0
        while 1:
            count += 1
            (ins, _, exs) = select.select(iw, ow, iw, 3)
            if exs:
                break
            if ins:
                for i in ins:
                    if i is soc:
                        out = self.connection
                    else:
                        out = soc
                    data = i.recv(self.rbufsize)
                    if data:
                        out.send(data)
                        count = 0
            #else:
            #    print "\t" "idle", count
            if count == max_idling:
                #self.server.log.debug("Reach timeout when retrieving %s" % (self.path))
                break

 ##### Request Handlers #####

    def do_GET(self):
        """
        """
        if self.authenticate('GET'):
            self.do_authenticated_GET()

    def do_HEAD(self):
        """
        """
        if self.authenticate('GET'):
            self.do_authenticated_GET()

    def do_DEL(self):
        """
        """
        if self.authenticate('GET'):
            self.do_authenticated_GET()

    def do_PUT(self):
        """
        """
        if self.authenticate('GET'):
            self.do_authenticated_GET()

    def do_POST(self):
        """
        """
        if self.authenticate('POST'):
            self.do_authenticated_GET()
            return True
