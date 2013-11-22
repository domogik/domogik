# -*- coding: utf-8 -*-

"""Module containing worker functionality for the MDP implementation.

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


import sys
import time
from pprint import pprint

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, DelayedCallback, PeriodicCallback

from domogik.mq.common import split_address
from domogik.mq.message import MQMessage
from domogik.mq.socket import ZmqSocket
try:
        from domogik.common.configloader import Loader
except ImportError:
        from domoweb.models import Parameter

class MQRep(object):

    """Class for the MDP worker side.

    Thin encapsulation of a zmq.DEALER socket.
    Provides a send method with optional timeout parameter.

    Will use a timeout to indicate a broker failure.
    """

    _proto_version = b'MDPW01'

    # TODO: integrate that into API
    HB_INTERVAL = 1000  # in milliseconds
    HB_LIVENESS = 3    # HBs to miss before connection counts as dead

    def __init__(self, context, service):
        """Initialize the MDPWorker.

        context is the zmq context to create the socket from.
        service is a byte-string with the service name.
        """
        if ("domogik.common.configloader" in sys.modules):
            cfg = Loader('mq').load()
            config = dict(cfg[1])
            self.endpoint = "tcp://{0}:{1}".format(config['ip'], config['req_rep_port'])
        else:
            ip = Parameter.objects.get(key='mq-ip')
            port = Parameter.objects.get(key='mq-req_rep_port')
            self.endpoint = "tcp://{0}:{1}".format(ip.value, port.value)
        self.context = context
        self.service = service
        self.stream = None
        self._tmo = None
        self.need_handshake = True
        self.ticker = None
        self._delayed_cb = None
        self._create_stream()
        return

    def _create_stream(self):
        """Helper to create the socket and the stream.
        """
        socket = ZmqSocket(self.context, zmq.DEALER)
        ioloop = IOLoop.instance()
        self.stream = ZMQStream(socket, ioloop)
        self.stream.on_recv(self._on_message)
        self.stream.socket.setsockopt(zmq.LINGER, 0)
        self.stream.connect(self.endpoint)
        self.ticker = PeriodicCallback(self._tick, self.HB_INTERVAL)
        self._send_ready()
        self.ticker.start()
        return

    def _send_ready(self):
        """Helper method to prepare and send the workers READY message.
        """
        ready_msg = [ b'', self._proto_version, b'\x01', self.service ]
        self.stream.send_multipart(ready_msg)
        self.curr_liveness = self.HB_LIVENESS
        return

    def _tick(self):
        """Method called every HB_INTERVAL milliseconds.
        """
        self.curr_liveness -= 1
        #print(('{0} tick - {1}'.format(time.time(), self.curr_liveness)))
        self.send_hb()
        if self.curr_liveness >= 0:
            return
        #print(('{0} lost connection'.format(time.time())))
        # ouch, connection seems to be dead
        self.shutdown()
        # try to recreate it
        self._delayed_cb = DelayedCallback(self._create_stream, 5000)
        self._delayed_cb.start()
        return

    def send_hb(self):
        """Construct and send HB message to broker.
        """
        msg = [ b'', self._proto_version, b'\x04' ]
        self.stream.send_multipart(msg)
        return

    def shutdown(self):
        """Method to deactivate the worker connection completely.

        Will delete the stream and the underlying socket.
        """
        if self.ticker:
            self.ticker.stop()
            self.ticker = None
        if not self.stream:
            return
        self.stream.socket.close()
        self.stream.close()
        self.stream = None
        self.timed_out = False
        self.need_handshake = True
        self.connected = False
        return

    def reply(self, msg):
        """Send the given message.

        msg can either be a byte-string or a list of byte-strings.
        """
##         if self.need_handshake:
##             raise ConnectionNotReadyError()
        # prepare full message
        to_send = self.envelope
        self.envelope = None
        if isinstance(msg, list):
            to_send.extend(msg)
        else:
            to_send.append(msg)
        self.stream.send_multipart(to_send)
        return

    def _on_message(self, msg):
        """Helper method called on message receive.

        msg is a list w/ the message parts
        """
        # 1st part is empty
        msg.pop(0)
        # 2nd part is protocol version
        # TODO: version check
        proto = msg.pop(0)
        # 3rd part is message type
        msg_type = msg.pop(0)
        # XXX: hardcoded message types!
        # any message resets the liveness counter
        self.need_handshake = False
        self.curr_liveness = self.HB_LIVENESS
        if msg_type == b'\x05': # disconnect
            self.curr_liveness = 0 # reconnect will be triggered by hb timer
        elif msg_type == b'\x02': # request
            # remaining parts are the user message
            envelope, msg = split_address(msg)
            envelope.append(b'')
            envelope = [ b'', self._proto_version, b'\x03'] + envelope # REPLY
            self.envelope = envelope
            mes = MQMessage()
            mes.set(msg)
            self.on_mdp_request(mes)
        else:
            # invalid message
            # ignored
            pass
        return

    def on_mdp_request(self, msg):
        """Public method called when a request arrived.

        Must be overloaded!
        """
        pass
#

### Local Variables:
### buffer-file-coding-system: utf-8
### mode: python
### End:
