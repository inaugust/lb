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
        typ=attrs['type']
        lb.levelfader[name]=levelfader (name, typ)

class levelfader(fader):

    def __init__(self, name, typ='min', callback=None, callback_arg=None,
                 groupname=None):
        fader.__init__(self, name, callback, callback_arg, groupname)
        self.typ=typ
        self.cue=None
        self.sourcedict=lb.get_sources(typ)

    def set_level(self, level):
        lb.send_signal('Level Fader Set Level', itself=self, level=level)
        #self.set_level_real({'level':level})
    
    def set_cue(self, cue):
        lb.send_signal('Level Fader Set Cue', itself=self, cue=cue)
        #self.set_cue_real({'cue':cue})
        
    def set_instrument(self, instrument):
        lb.send_signal('Level Fader Set Instrument', itself=self,
                       instrument=instrument)

    def set_type(self, cue):
        lb.send_signal('Level Fader Set Type', itself=self, typ=typ)

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
        print 'setting ',args['cue'], self.cue
        self.levellock.release()

    def set_instrument_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()

        self.cue=dummy()
        self.cue.matrix=lb.instrument[args['instrument']].get_matrix({'level':'100%'})
        self.levellock.release()
        
    def set_type_real(self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()

        self.typ=args['typ']
        self.sourcedict=lb.get_sources(self.typ)
        self.levellock.release()
        
    def act_on_set_ratio(self, ratio):
        # we have the lock
        self.matrix=self.cue.matrix*ratio

        if not self.callback:
            self.sourcedict[self.sourcename]=self.matrix
            lb.update_dimmers()
        
    def clear_real (self, args):
        self.wait_for()
        self.set_level_real({'level':0})
        self.cue=None
