import __main__
import sys
from threading import *
import string
import os

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
            #print 'Event: ' + signal
            #self.events.append('Event: ' + signal)
            self._queue_lock.release()
            for t in self._signals[signal]:
                if (args.has_key('itself')):
                    t(args['itself'], args)
                else:
                    t(args)

    def exit (self):
        self._terminated=1
        self.send_signal ('Shutdown')
        for lib in self._libraries:
            lib.shutdown()
            
