#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB forwarder

import zmq
from domogik.common.configloader import Loader

def main():
    cfg = Loader('messaging').load()
    cfg_messaging = dict(cfg[1])
    
    try:
        context = zmq.Context(1)
        # Socket facing emitters
        frontend = context.socket(zmq.SUB)
        # Forwarder subscribes to the emitter *pub* port
        frontend.bind("tcp://*:%s" % cfg_messaging['event_pub_port'])
        
        frontend.setsockopt(zmq.SUBSCRIBE, "") # We want to get all messages from emitters
        
        # Socket facing receivers
        backend = context.socket(zmq.PUB)
        # Forwarder publishes to the receiver *sub* port
        backend.bind("tcp://*:%s" % cfg_messaging['event_sub_port'])
        
        print("Forwarding messages...")
        zmq.device(zmq.FORWARDER, frontend, backend)
        

    except Exception, e:
        print(e)
        print("Bringing down ZMQ device")
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    print("PUB-SUB forwarder")
    main()
