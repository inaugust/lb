from xmllib import XMLParser
from os import path
import lightboard
import time
import attribute_widgets

from xml.parsers import expat
from ExpatXMLParser import ExpatXMLParser
from idl import LB

instrument_attributes = (
    'level',
    )

attribute_mapping = {
    'level': (LB.attr_level,
              attribute_widgets.LevelWidget,
              attribute_widgets.level_string_to_core,
              attribute_widgets.level_core_to_string),
    'time': (None, 
             None,
             attribute_widgets.time_string_to_core,
             attribute_widgets.time_core_to_string)
    }


def initialize(lb):
    lb.instrument={}
    try:
        f=open(path.join(lb.datapath, 'instruments'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()

def shutdown():
    pass

class parser(ExpatXMLParser):
    def start_instrument (self, attrs):
        lb.instrument[attrs['name']]=instrument(attrs['name'],
                                                attrs['core'],
                                                int(attrs['dimmer']))
        
class instrument:

    attributes=('level',)

    def __init__(self, name, corename, dimmer_number):
        print name
        self.name=name
        self.corename=corename
        self.dimmer_number=dimmer_number
        print 'get'
        self.coreinstrument=lb.get_instrument(name)
        print 'got', self.coreinstrument
        if (self.coreinstrument is not None):
            e=0
            try:
                print 'exist'
                e=self.coreinstrument._non_existent()
                print 'exist'
            except:
                self.coreinstrument=None
            if (e): self.coreinstrument=None
        if (self.coreinstrument is None):
            print 'get core'
            c = lb.get_core(corename)
            print 'create'
            c.createInstrument (lb.show, name, dimmer_number)
            print 'done'
        self.coreinstrument=lb.get_instrument(name)
        
    #public

    def get_attribute (self, name):
        if name == 'level':
            return self.get_level()
        raise AttributeError, name
    
    def set_attribute (self, name, arg):
        if name == 'level':
            return self.set_level(arg)
        raise AttributeError, name
        
    def set_level (self, level):
        self.coreinstrument.setLevel (lb.level_to_percent(level))

    def get_level (self):
        return lb.percent_to_level(self.coreinstrument.getLevel ())
        
