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
=============

- Csv Helper for REST

Implements
==========

CsvHelper object



@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

class CsvHelper():
    """ Easy way to create a csv
    """

    def __init__(self):
        """ Init csv structure
        """
        self.data = ""

    def add_data(self, line):
        """ add line to data
        """
        self.data = "%s\n%s" % (self.data, line)

    def get(self):
        """ getter for all csv data created
        """
        return self.data
        
    

