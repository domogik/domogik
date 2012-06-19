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

Mini Scene

Implements
==========

- MiniScene

@author: Fritz <fritz.smh@gmail.com> Basilic <Basilic3@hotmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import subprocess


class SceneException(Exception):
    """
    Scene exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Scene:
   

    def __init__(self, log, callback):
        self._log = log
        self._callback = callback
        self._ser = None


    def open(self):
        """ open
            @param device :
        """
        print "ouverture du plugin"


    def close(self):
        """ close t
        """
        print "fermeture du plugin"

    def listen(self):
        """close
        """
        print "demarage du listen"
        self._read = True
        
    def stop_listen(self):
        """ rien du tout
        """
        print "arret du listen"
        self._read = False

def decode(message):
    """ dédage du message
    """
    print "%s" % message




if __name__ == "__main__":                                                      
                                                     
    obj = Scene(None, decode)
    obj.open()
    obj.listen()           


    
       


