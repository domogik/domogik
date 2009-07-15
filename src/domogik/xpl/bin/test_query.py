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

Quick test of Query config object

Implements
==========


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from domogik.xpl.lib.queryconfig import *
from domogik.xpl.lib.module import *
from domogik.xpl.lib.xplconnector import *

class query_test(xPLModule):
    def __init__(self):
        xPLModule.__init__(self, name = "query_test")
        self.xpl = Manager()
#        print "=== config 1 ==="
#        res = xPLResult()
#        query_obj = Query(self.xpl)
#        print "Send query for x10.heyu_cfg_path"
#        query_obj.query("x10","heyu_cfg_path", res)
#        print "Answer received for x10.heyu_cfg_path : %s" % res.get_value()
#
#        print "Send query for x10.all"
#        query_obj.query("x10","heyu_cfg_path", res)
#        print "Answer received for x10.all : %s" % res.get_value()
#        del(query_obj)
#        del(res)
#        print "=== config 1 FINI ==="
        Listener(self._cb, self.xpl,{})

    def _cb(self, message):
        res = xPLResult()
#        query_obj = Query(self.xpl)

        print "Send query for x10.heyu_cfg_path"
        mess = Message()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.config')
        mess.set_data_key('technology', 'x10')
        mess.set_data_key('element', 'heyu_cfg_path')
        mess.set_data_key('key', '')
        Listener(self._query_cb, self.__myxpl,{'schema': 'domogik.config', 'type': 'xpl-stat'})
        self.__myxpl.send(mess)

#        query_obj.query("x10","heyu_cfg_path", res)
        print "Answer received for x10.heyu_cfg_path : %s" % res.get_value()

        print "Send query for x10.all"
        query_obj.query("x10","heyu_cfg_path", res)
        print "Answer received for x10.all : %s" % res.get_value()

    def _query_cb(self, message):
        print "QUERY CB !!! %s " % message

if __name__ == "__main__":
    q = query_test()
