from threading import *
from xmllib import XMLParser
from ExpatXMLParser import ExpatXMLParser
from os import path
from levelfader import levelfader
import instrument
from Numeric import *

def initialize(lb):
    lb.crossfader={}
    try:
        f=open(path.join(lb.datapath, 'crossfaders'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()
    lb.add_signal ('Crossfader Set Level', crossfader.set_level_real)
    lb.add_signal ('Crossfader Run', crossfader.run_real)
    
def shutdown():
    pass

class parser(ExpatXMLParser):

    def start_crossfader (self, attrs):
        typ=attrs.get('type', 'min')
        self.crossfader=crossfader (attrs['name'], typ)

    def end_crossfader (self):
        lb.crossfader[self.crossfader.name]=self.crossfader

    def start_fader (self, attrs):
        name=self.crossfader.name+'.'+attrs['name']

        f=levelfader(name, callback=crossfader.fader_return_levels,
                callback_arg=self.crossfader, groupname='crossfader.'+self.crossfader.name)
        lb.levelfader[name]=f

        self.crossfader.levels[name]=lb.newmatrix()

        if attrs['direction']=='up':
            self.crossfader.up[name]=f
        elif attrs['direction']=='down':
            self.crossfader.down[name]=f
            
class crossfader:

    def __init__(self, name, typ='min'):
        self.name=name
        self.sourcename='crossfader.'+name
        self.sourcedict=lb.get_sources(typ)
        self.level=0
        self.typ=typ
        self.up={}
        self.down={}
        self.levels={} #1 entry per fader which is a dict of (ins, level) 
        self.mythread=None
        self.running=0
        self.update_count=Semaphore (0)
        self.running_fader_lock=Lock()
        self.running_fader_count=0
        self.threadlock=Lock()
        self.debug=[]

    def get_fader (self, name):
        if self.down.has_key(name):
            return self.down[name]
        if self.up.has_key(name):
            return self.up[name]

        name=self.name+'.'+name

        if self.down.has_key(name):
            return self.down[name]
        if self.up.has_key(name):
            return self.up[name]

        return None

    def get_up_faders (self):
        return self.up.values()

    def get_down_faders (self):
        return self.down.values()
    
    def set_level(self, level):
        lb.send_signal('Crossfader Set Level', itself=self, level=level)

    def run(self, uptime=0, downtime=0):
        lb.send_signal('Crossfader Run', itself=self, uptime=uptime,
                       downtime=downtime)
        
    #private
    
    def fader_return_levels(self, name, matrix):
        #print 'return levels', name, matrix
        if (matrix==None):
            #run is done
            self.running_fader_lock.acquire()
            self.running_fader_count=self.running_fader_count-1
            print self.running_fader_count
            if (self.running_fader_count==0):
                self.update_count.release()
            self.running_fader_lock.release()
            return
        self.levels[name]=matrix
        self.update_count.release()
        
    def update_levels_from_faders(self):
        self.matrix=lb.newmatrix()
        #print self.levels
        #print self.levels.values()
        for matrix in self.levels.values():
            self.matrix=self.matrix+matrix
        # self.sourcedict == lb.min_source, or somesuch
        self.sourcedict[self.sourcename]=self.matrix
        lb.update_dimmers()

    def set_level_real(self, args):
        self.threadlock.acquire()

        if (self.mythread != None):
            self.threadlock.release()
            return

        level=lb.make_level(args['level'])
        self.level=level

        for up in self.up.values():
            up.set_level(level)
        self.update_count.acquire()

        for down in self.down.values():
            down.set_level(lb.dimmer_range-level)
        self.update_count.acquire()

        self.update_levels_from_faders()

        self.threadlock.release()
        
    def run_real(self, args):
        self.threadlock.acquire()
        uptime=args['uptime']
        downtime=args['downtime']
        if (self.mythread):
            #self.stop()
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        else:
            self.running=1
            self.mythread=Thread (target=crossfader.do_run, args=(self,
                                                                  uptime,
                                                                  downtime))
            self.mythread.start()
        self.threadlock.release()

    def do_run(self, uptime, downtime):
        self.running_fader_lock.acquire()
        for up in self.up.values():
            print up
            self.running_fader_count=self.running_fader_count+1
            up.run(level='100%', time=uptime)
        for down in self.down.values():
            print down
            self.running_fader_count=self.running_fader_count+1
            down.run(level=0, time=downtime)
        self.running_fader_lock.release()
            
        while(1):
            self.update_count.acquire()
            # not locking here, because it will be set to zero
            # before the release (we only care about 0)
            if (self.running_fader_count):
                self.update_levels_from_faders()
            else:
                break

        print 'done'
        count=0
        for up in self.up.values():
            down=self.down.values()[count]
            down.set_cue(up.cue.name)
            down.set_level('100%')
            print 'wait'
            self.update_count.acquire()
            print 'go'
            up.clear()
            print 'wait'
            self.update_count.acquire()
            print 'go'
            self.update_levels_from_faders()
            count=count+1
        
        self.threadlock.acquire()
        self.mythread=None
        self.running=0
        self.threadlock.release()
        print 'bye'
        for d in self.debug:
            print d
        self.debug=[]
        
