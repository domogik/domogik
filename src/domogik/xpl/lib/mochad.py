import socket
import sys
import os
import commands


class Mochad():

    def __init__(self,host,port):
        # Connect to the socket
        self.s = None

        for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.s = socket.socket(af, socktype, proto)
            except socket.error, msg:
                self.s = None
                continue
            try:
                self.s.connect(sa)
            except socket.error, msg:
                self.s.close()
                self.s = None
                continue
            break
        if self.s is None:
            print 'could not open socket'
            sys.exit(1)

        child_pid = os.fork()
        if child_pid == 0:
            self.listener()
        else:
            return None

    def listener(self):
        while True:
            rawdata = self.s.recv(1024)
            mochad_cmd = rawdata.strip().split(' ')
            if mochad_cmd[2] == 'Rx' and mochad_cmd[3] == 'RF':
                #XplPlugin.__init__(self, name = 'mochadListener')
                ## Prepare xpl message
                #mess = XplMessage()
                #mess.set_type("xpl-trig")
                #mess.set_schema("x10.basic")
                #mess.add_data({"device" :  mochad_cmd[5]})
                #mess.add_data({"command" :  mochad_cmd[7]})
                #if len(mochad_cmd) > 8:
                #    mess.add_data({"level" : mochad_cmd[8]})

                ## Send xpl message
                #self.myxpl.send(mess)
                print "Received from RF : "+mochad_cmd[5]+" "+mochad_cmd[7]
                os.system("/usr/bin/xpl-sender -m xpl-trig -c x10.basic device="+mochad_cmd[5]+" command="+mochad_cmd[7])

    def sender(self):
        while True:
            print "Listening to stdin"
            data = sys.stdin.readline()
            data = data.strip().split(' ')
            if data[0] == 'pl':
                self.send(data[1],data[2])

    def send(self,address,order,supp=""):
        if order == 'bright' or order == 'dim':
            data = "pl "+address+" "+order+" "+supp+"\n"
        else:
            data = "pl "+address+" "+order+"\n"
        print "Send "+data+" to mochad"
        self.s.send(data)


if __name__ == '__main__':
    HOST = '127.0.0.1'    # The remote host
    PORT = 50007              # The same port as used by the server

    mymochad = Mochad(HOST,PORT)

    mymochad.sender()
