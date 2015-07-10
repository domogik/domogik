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

from domogik.scenario.parameters.abstract import AbstractParameter


class ComparisonOperatorParameter(AbstractParameter):
    """ This parameter  simply provides different operators
    List of operators can be restricted/extendded when instanciated using add_filter and set_list_of_values
    for entry name "operator"
    This class basically provides those operators : [ '<', '>', '==', '!=', '<=', '>=', 'is', 'in', 'not in' ]
    """

    def __init__(self, log=None, trigger=None):
        AbstractParameter.__init__(self, log, trigger)
        self.set_type("list")
        self.add_expected_entry("operator", "list", "Operator to use for comparison")
        list_operator = ['==', '<', '>', '<=', '>=', '!=']
        the_list = []
        for op in list_operator:
           the_list.append([op, op])
        self.set_list_of_values("operator", the_list)

    def evaluate(self):
        """ Return chosen operator, or none if no operator choosed yet
        """
        p = self.get_parameters()
        if "operator" in p:
            return p["operator"]
        else:
            return None


#Some basic tests
if __name__ == "__main__":
    import logging
    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)
    t = ComparisonOperatorParameter(logging, None)
    print("Expected entries : {0}".format(t.get_expected_entries()))
    print("Evaluate should be None : {0}".format(t.evaluate()))
    print("List of possible values is {0}".format(t.get_list_of_values()))
    print("==> Setting some wrong value for entry 'operator', should raise some error")
    data = {"operator": "BAD"}
    try:
        t.fill(data)
    except ValueError:
        print("Received ValueError as expected, now try with a good operator")
        t.fill({"operator": "<"})
        print("Evaluate should now return some string : {0}".format(t.evaluate()))
    else:
        print("I did not received the expected exception, check your code !")
