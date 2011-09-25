import socket
import sys
import os
import commands
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query



class Mochad(XplPlugin):

    def __init__(self,host,port):
        # Connect to the socket

        XplPlugin.__init__(self, name = 'mochad')

        self.mochad_socket = None

        self.host = host
        self.port = port

        self.connect()

        child_pid = os.fork()
        if child_pid == 0:
            self.listener()
        else:
            return None

    def connect(self):
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.mochad_socket = socket.socket(af, socktype, proto)
            except socket.error, msg:
                self.mochad_socket = None
                continue
            try:
                self.mochad_socket.connect(sa)
            except socket.error, msg:
                self.mochad_socket.close()
                self.mochad_socket = None
                continue
            break
        if self.mochad_socket is None:
            print('could not open socket')
            sys.exit(1)

    def listener(self):
        while True:
            try:
                rawdata = self.mochad_socket.recv(1024)
            except socket.error, msg:
                self.mochad_socket = None
                while self.mochad_socket is None:
                    self.connect()

            mochad_cmd = rawdata.strip().split(' ')
            if mochad_cmd[2] == 'Rx' and mochad_cmd[3] == 'RF':
                # Prepare xpl message
                mess = XplMessage()
                mess.set_type("xpl-trig")
                mess.set_schema("x10.basic")
                mess.add_data({"device" :  mochad_cmd[5]})
                mess.add_data({"command" :  mochad_cmd[7]})
                if len(mochad_cmd) > 8:
                    mess.add_data({"level" : mochad_cmd[8]})

                ## Send xpl message
                self.myxpl.send(mess)
                print("Received from RF : "+mochad_cmd[5]+" "+mochad_cmd[7])

    def sender(self):
        while True:
            print("Listening to stdin")
            data = sys.stdin.readline()
            data = data.strip().split(' ')
            if data[0] == 'pl':
                self.mochad_socket.nd(data[1],data[2])


    def send(self,address,order,supp=""):
        if order == 'bright' or order == 'dim':
            data = "pl "+address+" "+order+" "+supp+"\n"
        else:
            data = "pl "+address+" "+order+"\n"
        print("Send "+data+" to mochad")
        try:
            self.mochad_socket.send(data)
        except Exception as e:
            self.mochad_socket = None
            while self.mochad_socket is None:
                self.connect()
            self.mochad_socket.send(data)


if __name__ == '__main__':
    HOST = '127.0.0.1'    # The remote host
    PORT = 50007              # The same port as used by the server

    mymochad = Mochad(HOST,PORT)

    mymochad.sender()
