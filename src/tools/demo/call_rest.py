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

Module purpose
==============

Call rest module for inserting data

Implements
==========

@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import urllib


if __name__ == '__main__':
    ip = "127.0.0.1"
    port = "8080"
    data_file = "./demo_data.txt"

    file = open(data_file, "r")

    for request in file.read().split('\n'):
        print "len=" + str(len(request))
        if request[0:0] != "#" and len(request) != 0:
            print "[ " + request + " ]"
            data = urllib.urlopen("http://%s:%s%s" % (ip, port, request))
            print data.read()
    file.close()



