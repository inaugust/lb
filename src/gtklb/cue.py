from xmllib import XMLParser
from os import path
import string
import lightboard
from ExpatXMLParser import ExpatXMLParser
import operator
from gtk import *
from libglade import *
from completion import completion
import time

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
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.parent=None
        
    def start_instrument (self, attrs):
        for key, value in attrs.items():
            if key == "name": continue
            self.cue.instrument[attrs['name']]={}
            self.cue.instrument[attrs['name']][key]=value
            print attrs['name'], key, value

    def start_cue (self, attrs):
        self.cue=cue(attrs['name'])

    def end_cue (self):
        lb.cue[self.cue.name]=self.cue
        self.cue.validate()

    def start_parent (self, attrs):
        l = attrs['level']
        if l[-1]=='%':
            l=l[:-1]
        l=float(l)/100
        self.parent=['', l]

    def handle_data (self, data):
        if self.parent is not None:
            self.parent[0]=data

    def end_parent (self):
        self.cue.parents.append(self.parent)
        self.parent=None

class instrument_cue_proxy:
     def __init__ (self, name, cue):
         # name is the name of the instrument to proxy for
         # cue is the cue object being edited
         self.__dict__['instrument'] = lb.instrument[name]
         self.__dict__['cue'] = cue
         self.__dict__['name'] = name

     def __getattr__(self, name):
         c = self.__dict__['cue']
         n = self.__dict__['name']
         if (c.apparent.has_key(n)):
             if c.apparent[n].has_key(name):
                 return c.apparent[n][name]
         return ''

     def __setattr__(self, name, value):
         c = self.__dict__['cue']
         n = self.__dict__['name']
         i = self.__dict__['instrument']
         if (not c.instrument.has_key(n)):
             c.instrument[n]={}
         if (not c.apparent.has_key(n)):
             c.apparent[n]={}
         c.instrument[n][name]=value
         c.apparent[n][name]=value
         c.build_time=time.time()
         if c.live_updates:
             i.set_attribute(name, value)

   

class cue(completion):

    def __init__(self, name):
        self.my_locals={'lb': lb}
        completion.__init__(self, self.my_locals)
        self.instrument={}
        self.apparent={}
        self.valid=0
        self.build_time=0
        self.parents=[]
        self.name=name
        self.core_cue = LB.Cue(name, [])
        self.live_updates=0
        self.create_window()

    def validate(self):
        for name, lvl in self.parents:
            lb.cue[name].validate()
        for name, lvl in self.parents:
            if (lb.cue[name].build_time <= self.build_time):
                continue
            if (self.valid):
                self.apparent={}
                self.valid=0
            for name, idict in lb.cue[name].apparent.items():
                if (not self.apparent.has_key(name)):
                    self.apparent[name]={}
                for attr, value in idict.items():
                    if (attr=='level'):
                        value = lb.percent_to_level (lb.level_to_percent (value) * lvl)
                    self.apparent[name][attr]=value
        if (not self.valid):
            for name, idict in self.instrument.items():
                if (not self.apparent.has_key(name)):
                    self.apparent[name]={}
                for attr, value in idict.items():
                    self.apparent[name][attr]=value
            self.to_core()
            self.valid=1
            self.build_time=time.time()
        
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

        for (name, dict) in incue.apparent.items():
            i = LB.InstAttrs(name, lb.instrument[name].coreinstrument, [])
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

    def edit(self):
        threads_enter()
        attrs = ['level']
        ins_in_cue = []
        for name, dict in self.apparent.items():
            l=[name]
            ins_in_cue.append(name)
            for a in attrs:
                if (dict.has_key(a)):
                    l.append(dict[a])
                else:
                    l.append('')
            self.in_tree.append (l)
        l = lb.instrument.keys()
        l.sort()
        for name in l:
            if (name not in ins_in_cue):
                #print name
                item = GtkTreeItem(name)
                item.show()
                self.out_tree.append(item)
            p = instrument_cue_proxy(name, self)
            self.my_locals[name]=p
        self.window.show()
        threads_leave()

    def test(self):
        print self.instrument
        print self.apparent

        attrs = ['level']
        for name, dict in self.apparent.items():
            l=[name]
            print name
            for a in attrs:
                if (dict.has_key(a)):
                    l.append(dict[a])
                else:
                    l.append('')
            print l

    def create_window(self):
        threads_enter()
        wTree = GladeXML ("gtklb.glade",
                          "cueEdit")
        dic = {"on_entry_activate": self.entry_activated,
               "on_entry_key_press_event": self.key_pressed}
        wTree.signal_autoconnect (dic)
        self.textbox = wTree.get_widget ("outputText")
        self.entry = wTree.get_widget ("entry")
        self.more_toggle = wTree.get_widget ("entryMore")
        self.out_tree = wTree.get_widget ("outTree")
        self.in_tree = wTree.get_widget ("inTree")
        self.window = wTree.get_widget ("cueEdit")
        threads_leave()
