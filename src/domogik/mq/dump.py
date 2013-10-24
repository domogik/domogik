import zmq
from domogik.mq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop

class MQSniffer(MQAsyncSub):

    def __init__(self):
       # parser = OptionParser()
       # parser.add_option("-c", action="store_true", dest="compress", \
       #         default=False, help="Diaply data in a compress way")
       # parser.add_option("-t", action="store", dest="xpltype", \
       #         default=None, type="string", \
       #         help="Filter messages on XPL message type")
       # parser.add_option("-s", action="store", dest="xplsource", \
       #         default=None, type="string", \
       #         help="Filter messages on XPL source field")
       # parser.add_option("-S", action="store", dest="xplschema", \
       #         default=None, type="string", \
       #         help="Filter messages on XPL schema field")
       # parser.add_option("-i", action="store", dest="xplinstance", \
       #         default=None, type="string", \
       #         help="Filter messages on XPL instance")
        MQAsyncSub.__init__(self, zmq.Context(), 'mqdump', '')
        IOLoop.instance().start()
        
    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))
        print(u"")

def main():
    s = MQSniffer()
         
if __name__ == "__main__":
    main()
