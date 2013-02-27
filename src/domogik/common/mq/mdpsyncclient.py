# -*- coding: utf-8 -*-

"""Module containing client functionality for the MDP implementation.

For the MDP specification see: http://rfc.zeromq.org/spec:7
"""

__license__ = """
    This file is part of MDP.

    MDP is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    MDP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with MDP.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = 'Guido Goldstein'
__email__ = 'gst-py@a-nugget.de'


import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, DelayedCallback

###

class MDPSyncClient(object):

    """Class for the MDP client side.

    Thin asynchronous encapsulation of a zmq.REQ socket.
    Provides a :func:`request` method with optional timeout.

    Objects of this class are ment to be integrated into the
    asynchronous IOLoop of pyzmq.

    :param context:  the ZeroMQ context to create the socket in.
    :type context:   zmq.Context
    :param endpoint: the enpoint to connect to.
    :type endpoint:  str
    :param service:  the service the client should use
    :type service:   str
    """

    _proto_version = b'MDPC01'

    def __init__(self, context, endpoint):
        """Initialize the MDPClient.
        """
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(endpoint)         
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        return

    def shutdown(self):
        """Method to deactivate the client connection completely.

        Will delete the stream and the underlying socket.

        .. warning:: The instance MUST not be used after :func:`shutdown` has been called.

        :rtype: None
        """
        if not self.socket:
            return
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()
        self.socket = None
        return

    def request(self, service, msg, timeout=None):
        """Send the given message.

        :param msg:     message parts to send.
        :type msg:      list of str
        :param timeout: time to wait in milliseconds.
        :type timeout:  int
        
        :rtype : message parts
        """
        if type(msg) in (bytes, unicode):
            msg = [msg]
        # prepare full message
        to_send = [self._proto_version, service]
        to_send.extend(msg)
        # send the message
        self.socket.send_multipart(to_send)
        # wait for receiving of the answer
        recv = None
        run = True
        while run:
            socks = dict(self.poller.poll(timeout))
            if socks:
                if socks.get(self.socket) == zmq.POLLIN:
                    recv = self.socket.recv_multipart()
            else:
                recv = None
                run = False
        # strip header (proto, service)
        
        # return msg
        return recv
