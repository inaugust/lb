import __main__
import sys
from threading import *
import string
import os

import SocketServer
import xmlrpcserver
import xmlrpclib

def make_time(time):
    try:
        time=float(time)
        return time
    except:
        time=str(time)
    if(string.lower(time[-1])=='s'):
        return float(time[:-1])
    if(string.lower(time[-1])=='m'):
        return float(time[:-1])*60
    if(string.lower(time[-1])=='h'):
        return float(time[:-1])*60*60
    ftime=0.0
    multiple=1.0
    l=string.rfind(time, ':')
    while (l!=-1):
        n=float(time[l+1:])
        ftime=ftime+(n*multiple)
        time=time[:l]
        multiple=multiple*60.0
        if (multiple>3600):
            return None
        l=string.rfind(time, ':')
    if (len(time)):
        ftime=ftime+(float(time)*multiple)
    return ftime

class lightboard:

    _signals={}
    _event_queue=[]
    _libraries=[]

    _queue_lock=None
    _queue_count=None

    _terminated=0

    def __init__(self, datapath):
        self.datapath=datapath
        __builtins__['lb']=self
        self.add_signal('Shutdown', None)
        self._queue_lock=Semaphore (1)
        self._queue_count=Semaphore (0)
        self.events=[]
        
    def load_libraries(self, libs):
        for lib in libs:
            print "Loading library: " + lib
            l=__import__(lib, globals(), locals(), [])
            l.initialize(self)
            self._libraries.append(l)
            

    def get_ins(self, name):
        ins = self.instrument[name]
        print 'r', ins
        return ins

    def add_signal (self, name, target):
        if (name not in self._signals.keys()):
            self._signals[name]=[]
        if (target):
            self._signals[name].append(target)

    def send_signal (self, name, **args):
        #print name
        self._queue_lock.acquire()
        self._event_queue.append((name, args))
        self._queue_lock.release()
        self._queue_count.release()

    def start(self):
        try:
            os.nice(-19)
        except:
            pass
        while not self._terminated:
            self._queue_count.acquire()
            self._queue_lock.acquire()
            signal,args = self._event_queue.pop(0)
            print 'Event: ' + signal
            #self.events.append('Event: ' + signal)
            self._queue_lock.release()
            for t in self._signals[signal]:
                if (type(t)==type('')):
                    client = xmlrpclib.Server(t)
                    if (args.has_key('itself')):
                        nargs=args.copy()
                        nargs['itself']=args['itself'].get_path()
                        client.send_signal([signal], nargs)
                    else:
                        client.send_signal([signal], args)
                else:
                    if (args.has_key('itself')):
                        t(args['itself'], args)
                    else:
                        t(args)

    def exit (self):
        self._terminated=1
        self.send_signal ('Shutdown')
        for lib in self._libraries:
            lib.shutdown()
            

class LBRequestHandler(xmlrpcserver.RequestHandler):
    def call(self, method, params):
        print self.path
        path_elements = string.split (self.path, '/')
        root=lb
        for e in path_elements:
            if not e:
                continue
            if (type(root)==type({})):
                root=root[e]
            else:
                root=getattr(root, e)

        print "Dispatching: ", root, method, params
        try:
            server_method = getattr(root, method)
        except:
            raise AttributeError, "Server does not contain XML-RPC procedure %s" % method
        if len(params)==1:
            r=apply(server_method, params[0])
        else:
            r=apply(server_method, params[0], params[1])
        if (r==None):
            return 0
        return r



