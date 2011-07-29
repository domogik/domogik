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

Plugin purpose
==============

TTS (Text To Speech)

Implements
==========

- TTS

@author: Gizmo  - Guillaume MORLET <contact@gizmo-network.fr>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
from subprocess import Popen



class Tts:
    """ TTS Text To Speech
    """
    

    def __init__(self, log = None, software = None):
        """ Init TTS
        """
        self._log = log
 	self.status_send = 0
	self.status_error = ""
	if software == None:
	    self.software = "espeak -v fr %s"
	else:
	    self.software = software

    def send(self,speech):
	print self.software
	msg = self.software % speech
	cmd = Popen(msg, shell=True)
	cmd.communicate()
	return 1

if __name__ == "__main__":
    my_tts = Tts(None)    
    my_tts.send("il y a eu un appel en absence")

