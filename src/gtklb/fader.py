# Base class for things that fade - that is, they have a start point,
# and end point, points in between, and a time in which to move through
# all of those points.

from threading import *
from xmllib import XMLParser
from os import path
import instrument
import lightboard
import time
import math
from gtk import *

def initialize():
    threads_enter()

    fader_menu_item=GtkMenuItem("Fader")
    lb.menubar.append(fader_menu_item)
    lb.fader_menu=GtkMenu()
    fader_menu_item.set_submenu(lb.fader_menu)

    lb.menubar.show_all()
    threads_leave()

def reset():
    pass

def shutdown():
    pass

def load(tree):
    pass

def save():
    pass

class fader:
    def __init__(self, name, callback=None, callback_arg=None, groupname=None):
        self.name=name
        if (groupname):
            self.sourcename=(groupname, 'fader.'+name)
        else:
            self.sourcename='fader.'+name
        self.level=0
        self.mythread=None
        self.callback=callback
        self.callback_arg=callback_arg
        self.threadlock=Lock()
        self.levellock=Lock()

    def set_level(self, level):
        # send signal to set_level_real
        pass

    def run(self, level, time=0):
        # send signal to run_real
        pass

    def stop(self):
        # send signal to stop_real        
        pass

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
    
    def set_level_real(self, args):
        self.levellock.acquire()
        level=lb.make_level(args['level'])
        self.level=level
        ratio=float(level)/float(lb.dimmer_range)

        self.act_on_set_ratio (ratio)
                
        if (self.callback):
            self.callback(self.callback_arg, self.name, self.matrix)

        self.levellock.release()

    def act_on_set_ratio(self, ratio):
        # talk to instruments here...
        pass
        
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
        start=time.time()
        level=fromlevel
        if (tolevel-fromlevel==0):
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

        mylevel=level
        mytime=start
        for s in range (0, steps):
            mylevel=mylevel+delta
            mytime=mytime+delay
            times[s]=(mylevel, mytime)

        for (target_level, target_time) in times:
            time.sleep (max(target_time-time.time(),0))
            self.set_level(target_level)
                        
        end=time.time()
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

