from xmllib import XMLParser
from os import path
import string
import lightboard
from ExpatXMLParser import ExpatXMLParser
import operator

from omniORB import CORBA
from idl import LB, LB__POA

def initialize(lb):
    lb.cue={}
    try:
        f=open(path.join(lb.datapath, 'cues'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()
        
def shutdown():
    pass

def sort_by_attr(seq, attr):
    intermed = map(None, map(getattr, seq, (attr,)*len(seq)),
                   xrange(len(seq)), seq)
    intermed.sort()
    return map(operator.getitem, intermed, (-1,) * len(intermed))


class parser(ExpatXMLParser):
    def start_instrument (self, attrs):
        d={}
        for key, value in attrs.items():
            if key == "name": continue
            d[key]=value
        self.cue.instrument[attrs['name']]=d

    def start_cue (self, attrs):
        self.cue=cue(attrs['name'])

    def end_cue (self):
        lb.cue[self.cue.name]=self.cue
        self.cue.core_cue = self.cue.to_core()

class cue:

    def __init__(self, name):
        self.instrument={}
        self.name=name
        self.core_cue = LB.Cue(name, [])

    def sl_level(self, s):
        return [lb.level_to_percent(s)]

    def ls_level(self, l):
        return '0'
        #return str(l[0])

    def sl_target(self, s):
        s=string.split(s[1:-1])
        return [10, 10, 10]
        #FIXME!
        #return [float(s[0]), float(s[1]), float(s[2])]

    def ls_target(self, l):
        return '('+str(l[0])+', '+str(l[1])+', '+str(l[2])+')'


    def copy(self):
        c = cue(self.name)
        c.instrument=self.instrument.copy()
        return c
    
    def to_core(self):
        incue = self
        cue = LB.Cue(self.name, [])

        for (name, dict) in incue.instrument.items():
            i = LB.InstAttrs(name, [])
            for (attr, value) in dict.items():
                if (attr=="level"):
                    a=LB.AttrValue(LB.attr_level, self.sl_level(value))
                if (attr=="target"):
                    a=LB.AttrValue(LB.attr_target, self.sl_target(value))
                if (attr=="focus"):
                    a=LB.AttrValue(LB.attr_focus, [])
                if (attr=="color"):
                    a=LB.AttrValue(LB.attr_color, [])
                if (attr=="gobo"):
                    a=LB.AttrValue(LB.attr_gobo, [])
                i.attrs.append(a)
            i.attrs=sort_by_attr(i.attrs, 'attr')
            cue.ins.append(i)
        cue.ins=sort_by_attr(cue.ins, 'name')            
        return cue
    
    def normalize(self, other):
        print "DON'T CALL NORMALIZE!"
        print "DON'T CALL NORMALIZE!"
        print "DON'T CALL NORMALIZE!"
        print "DON'T CALL NORMALIZE!"
        print "DON'T CALL NORMALIZE!"
        
        cue1=self.copy()
        cue2=other.copy()
        print "normalizing ", cue2.name, " to ", cue1.name
                
        # Any instrument in the start, but not in the end cue
        # should be faded to 0
        # Naturally, that won't actually happen if the fader doesn't
        # watch levels.
        start=time.time()
        for (name, dict) in cue1.instrument.items():
            print name
            if name not in cue2.instrument.keys():
                print name
                cue2.instrument[name]={'level': 0}
        end=time.time()
        print 'part1', end-start

        # Any instrument in the end, but not in the start cue
        # needs to have a starting position assigned in the start cue

        start=time.time()
        for (name, dict) in cue2.instrument.items():
            if name not in cue1.instrument.keys():
                cue1.instrument[name]={}
                #print name, type(name)
                i=lb.instrument[str(name)]
                for attr in dict.keys():
                    a=None
                    if (attr=="level"):
                        a=self.ls_level(i.getLevel())
                    if (attr=="target"):
                        a=self.ls_target(i.getTarget())
                    if (attr=="focus"):
                        a=''
                    if (attr=="color"):
                        a=''
                    if (attr=="gobo"):
                        a=''
                    cue1.instrument[name][attr]=a
        end=time.time()                    
        print 'part2', end-start

        start=time.time()                    
        r = (self.to_core(cue1), self.to_core(cue2))
        end=time.time()                    
        print 'part3', end-start
        return r
    
