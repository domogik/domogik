
import zmq
import json
from time import time
from domogik.common.configloader import Loader

MSG_VERSION = "0_1"

class MQPub(object):
    def __init__(self, context, caller_id):
        self.caller_id = caller_id
        cfg = Loader('mq').load()
        self.cfg_mq = dict(cfg[1])
        self.s_send = context.socket(zmq.PUB)
        pub_addr= "tcp://{0}:{1}".format(self.cfg_mq['ip'], self.cfg_mq['pub_port'])
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

