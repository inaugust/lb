#!/usr/bin/python

from threading import *
from Numeric import *
#import SocketServer
import socket
import sys

libraries=(
    'dimmer',
    'instrument',
    'moving_instrument',
    'cue',
    'levelfader',
    'transitionfader',
    'crossfader',
    'program',
    'procedure',
    'process',
    'keyboard',
#    'gtkui',
    )

from lightboard import lightboard #, LBRequestHandler

show='show'

lb = lightboard(show)
lb.load_libraries(libraries)


# class MyServer(SocketServer.TCPServer):
#     def server_bind(self):
#         self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         apply(SocketServer.TCPServer.server_bind, (self,))
        
# server = MyServer(('', 8000), LBRequestHandler)
# t=Thread (target=server.serve_forever)
#t.start()

#sys.exit(0)
lb.start()

