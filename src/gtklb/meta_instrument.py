# <meta_instrument name = "foo">
#   <instrument attributes="level" driver="name" name="lamp" .../>
#   <instrument attributes="color" driver="gel_scroller" name="scroller" .../>
# </meta_instrument>

import lightboard
import time
import string
import attribute_widgets
import instrument
from ExpatXMLParser import ExpatXMLParser, DOMNode
from idl import LB

def initialize():
    lb.instrument_module_info['Meta Instrument'] = instrument_info

def reset():
    pass

def shutdown():
    pass


def load_clump(tree, group = None):
    for ins in tree.find("meta_instrument"):
        subs={}
        attr_list = []
        for subins in ins.find("instrument"):
            sub = instrument.Instrument(subins.attrs, group=None, hidden=1)
            small_attr_list = map(string.strip,string.split(subins.attrs['attributes'], ','))
            attr_list = attr_list + small_attr_list
            for attr in small_attr_list:
                subs[attr]=sub
        i=MetaInstrument(ins.attrs, attr_list, subs, group)

def load(tree):
    for section in tree.find("instruments"):
        load_clump(section)
        for group in section.find("group"):
            load_clump(group, group.attrs['name'])
        
def save():
    # instrument's routine is sufficient
    pass
        
class MetaInstrument(instrument.Instrument):

    attributes=('level',)
    module='meta_instrument'

    def __init__(self, args, attr_list, subs, group = None):
        self.parent = None
        self.group = group
        self.hidden = 0
        self.name = args['name']
        self.attributes = tuple(attr_list)
        self.subinstrument = subs
        for sub in subs.values():
            sub.parent = self
        
        if group is not None:
            if not lb.instrument_group.has_key(group):
                lb.instrument_group[group]={}
            lb.instrument_group[group][self.name]=self
        else:
            lb.instrument_group[None][self.name]=self
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
    

class InstrumentInfo:
    container = 1
    module = 'meta_instrument'
    clazz = MetaInstrument
    allowable_children = ['instrument']

    def load(self, tree):
        load(tree)

    def get_arguments(self, ins):
        dict = {'name': ['', '']}
        for name, value in dict.items():
            if ins.attrs.has_key(name):
                dict[name][0]=ins.attrs[name]
        return dict

    def get_arguments_for_children(self, ins):
        dict = {'attributes': ['', '']}
        for name, value in dict.items():
            if ins.attrs.has_key(name):
                dict[name][0]=ins.attrs[name]
        return dict


instrument_info = InstrumentInfo()
