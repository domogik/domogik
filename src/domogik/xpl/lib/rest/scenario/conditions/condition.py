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

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.lib.rest.scenario.conditions.abstract import AbstractCondition

class Condition(AbstractCondition):
    """ We have nothing to extend right now
    """
    pass

if __name__ == "__main__":
    import logging
    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)

    from domogik.xpl.lib.rest.scenario.tests.textinpage import TextInPageTest
    c = None

    def mytrigger(test):
        logging.warning("Trigger called by test %s, refreshing state" % test)
        if c.get_parsed_condition() == None:
            return
        st = c.eval_condition()
        logging.warning("state of condition '%s' is %s" % (c.get_parsed_condition(), st))

    cond1 = """{ "NOT": {
        "990137de-25c9-4d47-8598-bb2eaec18e35": {
            "url": { 
                "urlpath": "http://localhost/index.html",
                "interval": "5"
            },
            "text": {
                "text": "nginx"
            }
        }
    }
    }"""
    mapping = {}
    mapping['990137de-25c9-4d47-8598-bb2eaec18e35'] = TextInPageTest(logging, trigger = mytrigger)
    c = Condition(logging, cond1, mapping)
    print "Condition created : %s" % c
    print "Trying to parse the condition ..."
    pc = c.parse_condition()
    print "Condition parsed, result is %s, condition is %s " % (pc, c.get_parsed_condition())
