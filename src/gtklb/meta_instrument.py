# <meta_instrument name = "foo">
#   <instrument attributes="level" driver="name" name="lamp" .../>
#   <instrument attributes="color" driver="gel_scroller" name="scroller" .../>
# </meta_instrument>

import lightboard
import time
import string
import attribute_widgets
from instrument import Instrument
from ExpatXMLParser import ExpatXMLParser, DOMNode
from idl import LB

def initialize():
    pass

def reset():
    pass

def shutdown():
    pass

def load(tree):
    for section in tree.find("instruments"):
        for ins in section.find("meta_instrument"):
            subs={}
            attr_list = []
            for subins in ins.find("instrument"):
                sub = Instrument(subins.attrs)
                attr_list = attr_list + map(string.strip,string.split(subins.attrs['attributes'], ','))
                for attr in attr_list:
                    subs[attr]=sub
            i=MetaInstrument(ins.attrs, attr_list, subs)
                         
def save():
    # instrument's routine is sufficient
    pass

        
class MetaInstrument(Instrument):

    attributes=('level',)
    module='meta_instrument'

    def __init__(self, args, attr_list, subs):
        self.name = args['name']
        self.attributes = tuple(attr_list)
        self.subinstrument = subs
        
        if (lb.instrument.has_key(self.name)):
            pass
        lb.instrument[self.name]=self

    #public

    def to_tree(self):
        instrument = DOMNode(self.module, {'name':self.name})
        subs = {}
        for a,i in self.subinstrument.items():
            if subs.has_key(i):
                subs[i]=subs[i]+', '+a
            else:
                subs[i]=a
        for i,a in subs.items():
            n = i.to_tree()
            n.attrs['attributes']=a
            instrument.append(n)
        return instrument

    def set_level (self, level):
        self.subinstrument['level'].set_level(level)
        
    def get_level (self):
        return self.subinstrument['level'].get_level()        

    def set_color (self, color):
        self.subinstrument['color'].set_level(level)
        
    def get_color (self):
        return self.subinstrument['color'].get_level()        

    def set_gobo_rpm (self, level):
        self.subinstrument['gobo_rpm'].set_gobo_rpm(level)
        
    def get_gobo_rpm (self):
        return self.subinstrument['gobo_rpm'].get_gobo_rpm()

    def to_core_InstAttrs (self, attr_dict):
        """ Used by Cues to create a core cue. """

        ret = []
        
        for attr, value in attr_dict.items():
            ret = ret + self.subinstrument[attr].to_core_InstAttrs({attr: value})

        return ret
    
