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

Get informations about one wire network

Implements
==========

class HelperError(Exception)
class Helper()

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import urllib

class HelperError(Exception):
    """ Helper exceptions
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Helper():
    """ Generic class for helpers
    """

    def __init__(self):
        """ Init helper
        """
        print("Init !")
        self.commands =   {}

    def help(self):
        """ Display help
        """
        data = []
        for cmd in self.commands:
            data.append("%s : %s" % (cmd, self.commands[cmd]["desc"]))
            try:
                if self.commands[cmd]["min_args"] > 0:
                    data.append("  Usage : %s" % self.commands[cmd]["usage"])
            except KeyError:
                pass
        return data

    def command(self, cmd, args = None):
        """ Execute helper command
            @param cmd : command
            @param args : table containing args
        """
        if args == None:
            args = []
        cmd = cmd.lower()
        print("Helper : %s %s" % (cmd, str(args)))
        if cmd == "help":
            return self.help()
        if cmd == None:
            return self.help()

        # unquote parameters
        for idx, val in enumerate(args):
            args[idx] = unicode(urllib.unquote(val), "UTF-8")
            print("%s - %s - %s" % (str(idx), args[idx], 
                                    unicode(urllib.unquote(val), "UTF-8")))

        try:
            if len(args) < self.commands[cmd]["min_args"]:
                return ["Missing parameters.", 
                        "Usage : %s" % self.commands[cmd]["usage"]]
        except KeyError:
            # no min_args defined : it is not a problem :)
            pass
        try:
            return self.commands[cmd]["cb"](args)
        except KeyError:
            return ["Wrong option : %s" % cmd]
        except IndexError:
            return ["Missing argument"]
