from threading import *
import xmlrpclib
from lightboard import lightboard, LBRequestHandler
import SocketServer
import socket

lb = lightboard('')
print 'a'
class MyServer(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        apply(SocketServer.TCPServer.server_bind, (self,))
print 'b'
server = MyServer(('', 8001), LBRequestHandler)
print 'c'
t=Thread (target=server.serve_forever)
print 'd'
t.start()
print 'e'

def print_foo(self, args):
    print 'foo'

print 'add'

host = xmlrpclib.Server("http://localhost:8000/")
host.add_signal(['Instrument Set Attribute', 'http://localhost:8001/'])

print 'add2'

lb.add_signal('Instrument Set Attribute', print_foo)

print 'call'
testsvr = xmlrpclib.Server("http://localhost:8000/instrument/1")
testsvr.set_attribute([],{'attribute':'level', 'value':'50%', 'source':'a'})

print 'start'

lb.start()
