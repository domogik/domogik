

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.common.mq.mdpbroker import MDPBroker
from domogik.common.configloader import Loader
from domogik.common.daemonize import createDaemon

class DomogikBroker(MDPBroker):

    def __init__(self, context):
	cfg = Loader('mq')
        my_conf = cfg.load()
	config = dict(my_conf[1])
        MDPBroker.__init__(self, context, config['broker_uri'])


def main():
    createDaemon()
    context = zmq.Context()
    broker = DomogikBroker(context)
    IOLoop.instance().start()
    broker.shutdown()

if __name__ == '__main__':
    main()
