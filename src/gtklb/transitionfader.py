from threading import *
from xmllib import XMLParser
from ExpatXMLParser import ExpatXMLParser
from os import path
import instrument
import lightboard
import time
import math
import string
from fader import fader

def initialize(lb):
    lb.transitionfader={}
    try:
        f=open(path.join(lb.datapath, 'transitionfaders'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()
    lb.add_signal ('Transition Fader Set Start Cue', transitionfader.set_start_cue_real)
    lb.add_signal ('Transition Fader Set End Cue', transitionfader.set_end_cue_real)
    lb.add_signal ('Transition Fader Set Attributes', transitionfader.set_attributes_real)
    lb.add_signal ('Transition Fader Set Level',
                   transitionfader.set_level_real)
    lb.add_signal ('Transition Fader Run', transitionfader.run_real)
    lb.add_signal ('Transition Fader Stop', transitionfader.stop_real)
    lb.add_signal ('Transition Fader Clear', transitionfader.clear_real)
    
def shutdown():
    pass

class parser(ExpatXMLParser):

    def start_transitionfader (self, attrs):
        name=attrs['name']
        lb.transitionfader[name]=transitionfader (name)

class transitionfader(fader):

    supported_attributes = ['level', 'target']

    def __init__(self, name):
        fader.__init__(self, name, None, None, None)
        self.cue=None
        self.attributes=self.supported_attributes[:]
        self.start_cue_name=self.end_cue_name=None
        self.attribute_methods = {'level': self.do_set_level,
                                  'target': self.do_set_target,
                            #'color': transitionfader.do_set_color
                            }
            

    def set_level(self, level):
        #lb.send_signal('Transition Fader Set Level', itself=self, level=level)
        self.set_level_real({'level':level})
    
    def set_start_cue(self, cue):
        lb.send_signal('Transition Fader Set Start Cue', itself=self, cue=cue)
        #self.set_cue_real({'cue':cue})

    def set_end_cue(self, cue):
        lb.send_signal('Transition Fader Set End Cue', itself=self, cue=cue)
        #self.set_cue_real({'cue':cue})

    def set_attributes(self, attributes):
        lb.send_signal('Transition Fader Set Attributes', itself=self, attributes=attributes)
        
    def run(self, level, time=0):
        lb.send_signal('Transition Fader Run', itself=self, level=level, time=time)

    def stop(self):
        lb.send_signal('Transition Fader Stop', itself=self)

    def clear(self):
        lb.send_signal('Transition Fader Clear', itself=self)

    #private
    
    def set_start_cue_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()

        self.start_cue_name=args['cue']
        print 'setting ',args['cue'], self.cue
        self.fix_cues()
        self.levellock.release()

    def set_end_cue_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()

        self.end_cue_name=args['cue']
        print 'setting ',args['cue'], self.cue

        self.fix_cues()

        self.levellock.release()

    def set_attributes_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        self.levellock.acquire()
        self.attributes=args['attributes']
        self.fix_cues()
        self.levellock.release()

    def fix_cues (self):
        print 'start', self.start_cue_name
        print 'end', self.end_cue_name
        print 'attr', self.attributes
        starttime=time.time()
        if (self.start_cue_name == None or self.end_cue_name==None):
            return

        self.start_cue=lb.cue[self.start_cue_name].instrument.copy()
        self.end_cue=lb.cue[self.end_cue_name].instrument.copy()

        # Any instrument in the start, but not in the end cue
        # should be faded to 0
        # Naturally, that won't actually happen if the fader doesn't
        # watch levels.
        
        for (name, dict) in self.start_cue.items():
            if name not in self.end_cue.keys():
                self.end_cue[name]={'level': 0}

        # Any instrument in the end, but not in the start cue
        # needs to have a starting position assigned in the start cue

        for (name, dict) in self.end_cue.items():
            if name not in self.start_cue.keys():
                self.start_cue[name]={}
                for attr in dict.keys():
                    self.start_cue[name][attr]=lb.instrument[name].get_attribute(attribute=attr)

        # Do value conversion on the cues:
        
        for (name, dict) in self.start_cue.items():
            for attr, val in dict.items():
                if attr not in self.attributes:
                    del dict[attr]
                    continue
                if (attr=='level'):
                    dict[attr]=lb.instrument[name].make_level(val)
                elif (attr=='target'):
                    dict[attr]=map(lb.len_to_ft, string.split(val[1:-1], ','))

        for (name, dict) in self.end_cue.items():
            for attr, val in dict.items():
                if attr not in self.attributes:
                    del dict[attr]
                    continue
                if (attr=='level'):
                    dict[attr]=lb.instrument[name].make_level(val)
                elif (attr=='target'):
                    dict[attr]=map(lb.len_to_ft, string.split(val[1:-1], ','))

        cue={}
        for (name, dict) in self.end_cue.items():
            cue[lb.instrument[name]]=dict
        self.end_cue=cue
        cue={}
        for (name, dict) in self.start_cue.items():
            cue[lb.instrument[name]]=dict
        self.start_cue=cue
            
            
        endtime=time.time()
        print 'fixed cues in ', endtime-starttime
            
    def act_on_set_ratio(self, ratio):
        # we have the lock
        for (name, dict) in self.end_cue.items():
            for attr in dict.keys():
                # if attr in self.attributes:
                #print name, dict, attr, self.attributes
                self.attribute_methods[attr](name,
                                             self.start_cue[name][attr],
                                             dict[attr],
                                             ratio)
        lb.update_dimmers()

    def do_set_level(self, ins, start, end, ratio):
        #ins=lb.instrument[name]
        level=start+((end-start)*ratio)
        #print name, start, end, level, ratio
        ins.set_attribute_real({'attribute':'level', 'value':level,
                                'immediately':0,
                                'source':None, 'typ':min})

    def do_set_target(self, ins, start, end, ratio):
        #ins=lb.instrument[name]
        #print start, end
        pos=[((end[0]-start[0])*ratio),
             ((end[1]-start[1])*ratio),
             ((end[2]-start[2])*ratio)]
        #print name, start, end, pos, ratio
        ins.set_attribute_real({'attribute':'target', 'value':pos,
                                'immediately':0,
                                'source':None, 'typ':min})
        
        
    def clear_real (self, args):
        self.wait_for()
        self.set_level_real({'level':0})
        self.start_cue=None
        self.start_cue_name=None
        self.end_cue=None
        self.end_cue_name=None
