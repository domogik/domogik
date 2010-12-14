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

KNx Bus

Implements
==========

- KNX

@author: Fritz <fritz.smh@gmail.com> Basilic <Basilic3@hotmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import subprocess

class KNXException(Exception):
    """
    KNX exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class KNX:
   

    def __init__(self, log, callback):
        self._log = log
        self._callback = callback
        self._ser = None


    def open(self, device):
        """ open 
            @param device :
        """
        # device example : "ipt:192.168.0.148"
        command = "eibd -i -d -D %s" % device
        subp = subprocess.Popen(command, shell=True)        
        self.eibd_pid = subp.pid 

    def close(self):
        """ close t
        """
        subp = subprocess.Popen("kill %s" % self.eibd_pid, shell=True)   
        # TODOD : add check and kill -9 if necessary

    def listen(self):                                                   
        command = "groupsocketlisten ip:127.0.0.1"                               
        self.pipe = subprocess.Popen(command,                                   
                     shell = True,                                              
                     bufsize = 1024,                                            
                     stdout = subprocess.PIPE                                   
                     ).stdout                                                   
        self._read = True                                                       
                                                                                
        while self._read:                                                       
            data = self.pipe.readline()                                         
            if not data:                                                        
                break                                                           
            self._callback(data) 
            #print "> %s" % data                                                 
                                               
    def stop_listen(self):                                                      
        self._read = False 

    def read(self, groups):
        command2 = "groupread ip:127.0.0.1 %s" % groups                              
        subp2 = subprocess.Popen(command2, shell=True) 
 

    def write(self, groups, Value):
	
	if Value < 31:
		os.system("groupswrite ip:127.0.0.1 " % groups % Value)
	else:
		os.system("groupwrite ip:127.0.0.1 "%groups % Value)



def decode(message):
    ''' décodage du message
    '''
    print "%s" % message

if __name__ == "__main__":                                                      
    device = "ipt:192.168.0.148"                                                        
    obj = KNX(None, decode)                                                           
    obj.open(device)
    obj.listen()           


    
       


