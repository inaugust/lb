from os import path
import lightboard
import time

from ExpatXMLParser import ExpatXMLParser, DOMNode
from idl import LB

def initialize():
    reset()
    
def reset():
    lb.instrument={}

def shutdown():
    pass

def load(tree):
    for section in tree.find("instruments"):
        for ins in section.find("instrument"):
            i=Instrument(ins.attrs)
            
def save():
    tree = DOMNode('instruments')
    for i in lb.instrument.values():
        tree.append(i.to_tree())
    return tree

class Instrument:

    attributes=('level',)
    module='instrument'

    def __init__(self, args):
        self.name = args['name']
        self.driver = args['driver']
        self.corename = args['core']

        self.arglist = []
        for n,v in args.items():
            if n in ('name', 'driver', 'core'):
                continue
            self.arglist.append(LB.Argument(n,v))

        self.coreinstrument=lb.get_instrument(self.name)
        if (self.coreinstrument is not None):
            e=0
            try:
                e=self.coreinstrument._non_existent()
            except:
                self.coreinstrument=None
            if (e): self.coreinstrument=None
        if (self.coreinstrument is None):
            c = lb.get_core(self.corename)
            c.createInstrument (lb.show, self.name, self.driver, self.arglist)
            self.coreinstrument=lb.get_instrument(self.name)

        attrlist = []
        for attr in self.coreinstrument.getAttributes():
            for (name, t) in attribute_widgets.attribute_mapping.items():
                if t[0] == attr:
                    attrlist.append(name)
        self.attributes = tuple(attrlist)
        
        if (lb.instrument.has_key(self.name)):
            pass
        lb.instrument[self.name]=self

        
    #public

    def to_tree(self):
        dict = self.arglist.copy()
        dict['name']=self.name
        dict['driver']=self.driver
        dict['core']=self.corename

        instrument = DOMNode(self.module, dict)
        return instrument

    def get_attribute (self, name):
        if name == 'level':
            return self.get_level()
        raise AttributeError, name
    
    def set_attribute (self, name, arg):
        if name == 'level':
            return self.set_level(arg)
        raise AttributeError, name
        
    def set_level (self, level):
        self.coreinstrument.setLevel (lb.value_to_core('level', level)[0])

    def get_level (self):
        return lb.value_to_string('level', [self.coreinstrument.getLevel ()])
        
    def to_core_InstAttrs (self, attr_dict):
        """ Used by Cues to create a core cue.  But note how easily it
        can be overridden to return a list of several InstAttrs,
        so that you can have a kind of Meta-Instrument that controls more
        than one actual instrument. """
        
        i = LB.InstAttrs(self.name, self.coreinstrument, [])
        for (attr, value) in attr_dict.items():
            a = LB.AttrValue(lb.core_attr_id(attr),
                             lb.value_to_core(attr, value))
            i.attrs.append(a)
        i.attrs=lb.sort_by_attr(i.attrs, 'attr')
        return [i]
