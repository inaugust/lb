from threading import *
from xmllib import XMLParser
from os import path
import instrument
import lightboard
import time
import math

def initialize(lb):
    lb.fader={}
    try:
        f=open(path.join(lb.datapath, 'faders'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())
    lb.add_signal ('Fader Set Cue', fader.set_cue_real)
    lb.add_signal ('Fader Set Instrument', fader.set_instrument_real)
    lb.add_signal ('Fader Set Type', fader.set_type_real)
    lb.add_signal ('Fader Set Level', fader.set_level_real)
    lb.add_signal ('Fader Run', fader.run_real)
    lb.add_signal ('Fader Stop', fader.stop_real)
    lb.add_signal ('Fader Clear', fader.clear_real)
    
def shutdown():
    pass

class dummy:
    pass

class parser(XMLParser):

    def start_fader (self, attrs):
        name=attrs['name']
        type=attrs['type']
        lb.fader[name]=fader (name, type)

class fader:

    def __init__(self, name, type='min', callback=None, callback_arg=None):
        self.name=name
        self.sourcename='fader.'+name
        self.level=0
        self.type=type
        self.cue=None
        self.instrument={}
        self.mythread=None
        self.callback=callback
        self.callback_arg=callback_arg
        self.threadlock=Lock()
        self.levellock=Lock()

    def set_level(self, level):
        lb.send_signal('Fader Set Level', itself=self, level=level)

    def set_cue(self, cue):
        lb.send_signal('Fader Set Cue', itself=self, cue=cue)

    def set_instrument(self, instrument):
        lb.send_signal('Fader Set Instrument', itself=self,
                       instrument=instrument)

    def set_type(self, cue):
        lb.send_signal('Fader Set Type', itself=self, type=type)

    def run(self, level, time=0):
        lb.send_signal('Fader Run', itself=self, level=level, time=time)

    def stop(self):
        lb.send_signal('Fader Stop', itself=self)

    def clear(self):
        lb.send_signal('Fader Clear', itself=self)

    def wait_for (self):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            return
        self.threadlock.release()

    def is_running (self):
        self.threadlock.acquire()
        if (self.mythread):
            ret=1
        else:
            ret=0
        self.threadlock.release()
        return ret
        
        
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
            d={}
            for (attrname, attrval) in ins.items():
                d[attrname] = attrval
            self.instrument[name]=d
            
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
        d={}
        d['level'] = 0
        self.instrument[args['instrument']]=d
            
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
        
    def set_level_real(self, args):
        self.levellock.acquire()
        level=lb.make_level(args['level'])
        self.level=level
        ratio=float(level)/float(lb.dimmer_range)

        #print self.name+' '+str(level)

        if (self.cue): 
            for (name, ins) in self.cue.instrument.items():
                for (attrname, attrval) in ins.items():
                    setlevel=int(float(attrval)*ratio)
                    self.instrument[name][attrname]=setlevel
                    if (not self.callback):
                        instrument=lb.instrument[name]
                        instrument.set_attribute(attribute=attrname, value=setlevel, source=self.sourcename, type=self.type)
        else:
            for (name, dict) in self.instrument.items():
                ins = lb.instrument[name]
                dict['level']=level
                
        if (self.callback):
            self.callback(self.callback_arg, self.name, self.instrument)

        self.levellock.release()
        
    def run_real(self, args):
        self.threadlock.acquire()
        fromlevel=self.level
        tolevel=lb.make_level(args['level'])
        time=lightboard.make_time(args['time'])
        if (self.mythread):
            self.running=0
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        else:
            self.running=1
            self.mythread=Thread (target=fader.do_run, args=(self,
                                                             fromlevel,
                                                             tolevel,
                                                             time))
            self.mythread.start()
        self.threadlock.release()
        
    def do_run(self, fromlevel, tolevel, intime):
        print (self.name+' '+str(fromlevel) + ' to ' + str(tolevel))
        start=time.time()
        level=fromlevel
        if (tolevel-fromlevel==0):
            print 'nothing to do'
            self.threadlock.acquire()
            self.mythread=None
            self.threadlock.release()
            if (self.callback):
                self.callback(self.callback_arg, self.name, None)
            return
        if (tolevel-fromlevel)>0: delta=1
        else: delta=-1

        if (intime<=3):  delta=delta*int((1/(4*math.exp(intime-3)))+1.5)
        if (intime==0):
            self.set_level(tolevel)
            self.threadlock.acquire()
            self.mythread=None
            self.threadlock.release()
            if (self.callback):
                self.callback(self.callback_arg, self.name, None)
            return

        adelta=abs(delta)
        steps=abs(tolevel-fromlevel)/adelta

        endtime=start+intime
        delay=float(intime)/float(steps)
        times=range (0, steps)

        #print 'schedule'
        mylevel=level
        mytime=start
        for s in range (0, steps):
            mylevel=mylevel+delta
            mytime=mytime+delay
            #print str(mylevel) + ' @ ' + str(mytime)
            times[s]=(mylevel, mytime)

        #print 'running'

        for (target_level, target_time) in times:
            #print str(target_level) + ' @ ' + str(target_time) + ' s ' + str(max(target_time-time.time(),0))
            time.sleep (max(target_time-time.time(),0))
            self.set_level(target_level)
                        
        end=time.time()
        print (self.name+' '+str(fromlevel) + ' to ' + str(tolevel) + ' in '+
               str(end-start))
        self.threadlock.acquire()
        self.mythread=None
        self.threadlock.release()
        if (self.callback):
            self.callback(self.callback_arg, self.name, None)
                
    def stop_real(self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.running=0
            self.threadlock.release()
            self.mythread.join()
            return
        self.threadlock.release()

    def clear_real (self, args):
        self.wait_for()
        self.set_level_real({'level':0})
        self.cue=None
        self.instrument={}
