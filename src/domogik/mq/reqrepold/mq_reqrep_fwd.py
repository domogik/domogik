#!/usr/bin/python

# Message queuing broker in request / reply pattern

import zmq

def main():
    context = zmq.Context(1)
    
    # Socket facing clients
    frontend = context.socket(zmq.ROUTER)
    frontend.bind("tcp://*:6559")
    
    # Socket facing services
    backend = context.socket(zmq.DEALER)
    backend.bind("tcp://*:6560")
    
    print("Forwarding messages...")
    zmq.device(zmq.QUEUE, frontend, backend)

    # We never get here...
    frontend.close()
    backend.close()
    context.term()
    
if __name__ == "__main__":
    main()
