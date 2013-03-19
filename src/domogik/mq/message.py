"""MQMessage
   
   handler class to handle a reqrep message

   this wrapper is written to easely extend the message type later on,
"""

import json

class MQMessage():
    """MQMessage
       => part 0 = action (config.get, config,set, config.result)
       => part 1 = data
    """
    _action = None
    _data = {}

    def __init__(self, action=None, data=None):
        """ __init__
            can set action and data field
        """
        if action:
            self._action = action
        if data:
            self._data = data

    def setaction(self, action):
        """ setAction
            sets the action field
        """
        self._action = action

    def adddata(self, key, value):
        """ addData
            append a data element to the stack
        """
        self._data[key] = value

    def getaction(self):
        """ getAction
            returns the current action
        """
        return self._action

    def getdata(self):
        """ getData
            returns the current data
        """
        return self._data

    def get(self):
        """ get
            returns a compiled list
        """
        stack = []
        stack.append( self._action )
        stack.append( json.dumps(self._data) )
        return stack

    def set(self, stack):
        """ set
            input a message list and decompile
        """
        print stack
        self._action = stack.pop(0)
        print stack
        self._data = json.loads(stack.pop(0))

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<MQMessage(action=%s, data='%s')>" % (self._action, self._data)

