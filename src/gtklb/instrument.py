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


def initialize():
    reset()
    
def reset():
    lb.instrument={}

def shutdown():
    pass

def load(data):
    p=parser()
    p.Parse(data)
    p.close()
    
def save():
    s="<instruments>\n\n"
    for c in lb.instrument.values():
        s=s+c.to_xml(1)
    s=s+"</instruments>\n"
    return s

class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_instruments=0

    def start_instruments (self, attrs):
        self.in_instruments=1

    def end_instruments (self):
        self.in_instruments=0
        
    def start_instrument (self, attrs):
        if (not self.in_instruments):
            return
        lb.instrument[attrs['name']]=instrument(attrs['name'],
                                                attrs['core'],
                                                int(attrs['dimmer']))
        
class instrument:

    attributes=('level',)
    driver='instrument'

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

    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s=s+sp+'<%s name="%s" core="%s" dimmer="%s"/>\n' % (self.driver,
                                                           self.name,
                                                           self.corename,
                                                           self.dimmer_number)
        return s

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
        return lb.value_to_string('level', [self.coreinstrument.getLevel ()])
        
