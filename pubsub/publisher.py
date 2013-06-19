
import zmq
import json
import sys
from time import time
try:
    from domogik.common.configloader import Loader
except ImportError:
    from domoweb.models import Parameter

MSG_VERSION = "0_1"

class MQPub(object):
    def __init__(self, context, caller_id):
        if ("domogik.common.configloader" in sys.modules):
            cfg = Loader('mq').load()
            self.cfg_mq = dict(cfg[1])
            sub_addr= "tcp://{0}:{1}".format(self.cfg_mq['ip'], self.cfg_mq['pub_port'])
        else:
            ip = Parameter.objects.get(key='mq-ip')
            port = Parameter.objects.get(key='mq-pub_port')
            pub_addr= "tcp://{0}:{1}".format(ip.value, port.value)
        self.caller_id = caller_id
        self.s_send = context.socket(zmq.PUB)
        self.s_send.connect(pub_addr)

    def __del__(self):
        self.s_send.close()

    def send_event(self, category, content):
        """Send an event in in multi-part : first message id and then its content

        @param category : category of the message
        @param content : content of the message : must be in JSON format

        """
        msg_id = "%s.%s.%s" %(category, str(time()).replace('.','_'), MSG_VERSION)
        self.s_send.send(msg_id, zmq.SNDMORE)
        self.s_send.send( json.dumps(content) )

