from threading import *
from xmllib import XMLParser
from os import path
import instrument
import lightboard
import time
import math
from fader import fader

def initialize(lb):
    lb.levelfader={}
    try:
        f=open(path.join(lb.datapath, 'levelfaders'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())
    lb.add_signal ('Level Fader Set Cue', levelfader.set_cue_real)
    lb.add_signal ('Level Fader Set Instrument',
                   levelfader.set_instrument_real)
    lb.add_signal ('Level Fader Set Type', levelfader.set_type_real)
    lb.add_signal ('Level Fader Set Level', levelfader.set_level_real)
    lb.add_signal ('Level Fader Run', levelfader.run_real)
    lb.add_signal ('Level Fader Stop', levelfader.stop_real)
    lb.add_signal ('Level Fader Clear', levelfader.clear_real)
    
def shutdown():
    pass

class dummy:
    pass

class parser(XMLParser):

    def start_levelfader (self, attrs):
        name=attrs['name']
        type=attrs['type']
        lb.levelfader[name]=levelfader (name, type)

class levelfader(fader):

    def __init__(self, name, type='min', callback=None, callback_arg=None):
        fader.__init__(self, name, callback, callback_arg)
        self.type=type
        self.cue=None
        self.instrument={}

    def set_level(self, level):
        lb.send_signal('Level Fader Set Level', itself=self, level=level)

    def set_cue(self, cue):
        lb.send_signal('Level Fader Set Cue', itself=self, cue=cue)

    def set_instrument(self, instrument):
        lb.send_signal('Level Fader Set Instrument', itself=self,
                       instrument=instrument)

    def set_type(self, cue):
        lb.send_signal('Level Fader Set Type', itself=self, type=type)

    def run(self, level, time=0):
        lb.send_signal('Level Fader Run', itself=self, level=level, time=time)

    def stop(self):
        lb.send_signal('Level Fader Stop', itself=self)

    def clear(self):
        lb.send_signal('Level Fader Clear', itself=self)

    #private
    
    def set_cue_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()

        self.cue=lb.cue[args['cue']]
        self.instrument={}
        for (name, ins) in self.cue.instrument.items():
            self.instrument[name]=ins['level']
            
        self.levellock.release()

    def set_instrument_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()

        self.cue=None
        self.instrument={}
        self.instrument[args['instrument']]=0
            
        self.levellock.release()
        
    def set_type_real(self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()

        self.type=args['type']

        self.levellock.release()
        
    def act_on_set_ratio(self, ratio):
        # we have the lock

        if (self.cue): 
            for (name, ins) in self.cue.instrument.items():
                setlevel=int(float(ins['level'])*ratio)
                self.instrument[name]=setlevel
                if (not self.callback):
                    instrument=lb.instrument[name]
                    instrument.set_attribute(attribute='level', value=setlevel, source=self.sourcename, type=self.type)
        else:
            for (name, level) in self.instrument.items():
                ins = lb.instrument[name]
                self.instrument[name]=level

        # callback happens in calling function
        
    def clear_real (self, args):
        self.wait_for()
        self.set_level_real({'level':0})
        self.cue=None
        self.instrument={}
