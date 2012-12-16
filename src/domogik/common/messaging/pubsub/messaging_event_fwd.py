#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB forwarder

import zmq

def main():
    try:
        context = zmq.Context(1)
        # Socket facing emitters
        frontend = context.socket(zmq.SUB)
        frontend.bind("tcp://*:5559")
        
        frontend.setsockopt(zmq.SUBSCRIBE, "") # We want to get all messages from emitters
        
        # Socket facing receivers
        backend = context.socket(zmq.PUB)
        backend.bind("tcp://*:5560")
        
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
