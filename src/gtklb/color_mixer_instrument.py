# A subclass of instrument to demonstrate it's meta-ness.
# It's designed to represent three instruments, gelled RGB.
# When you set this instrument's color and level, it will set the
# appropriate levels of the other instruments.

from xmllib import XMLParser
from os import path
import lightboard
import time
import attribute_widgets
from instrument import instrument

from xml.parsers import expat
from ExpatXMLParser import ExpatXMLParser
from idl import LB

def initialize():
    pass

def reset():
    pass

def shutdown():
    pass

def load(data):
    p=parser()
    p.Parse(data)
    p.close()
    
def save():
    # instrument's routine is sufficient
    pass

class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_instruments=0

    def start_instruments (self, attrs):
        self.in_instruments=1

    def end_instruments (self):
        self.in_instruments=0
        
    def start_color_mixer_instrument (self, attrs):
        if (not self.in_instruments):
            return
        name = attrs['name']
        red =  attrs['red']
        green = attrs['green']
        blue = attrs['blue']
        lb.instrument[attrs['name']]=color_mixer_instrument(name,
                                                            red, green, blue)
        
        
class color_mixer_instrument(instrument):

    attributes=('level','color',)
    driver='color_mixer_instrument'

    def __init__(self, name, red, green, blue):
        self.name=name
        self.red_name = red
        self.green_name = green
        self.blue_name = blue
        self.level = [0.0]
        self.color = [0.0, 0.0, 0.0]
        
    #public

    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s=s+sp+'<%s name="%s" red="%s" green="%s" blue="%s"/>\n' % (self.driver, self.name, self.red_name, self.green_name, self.blue_name)
        return s

    def set_level (self, level):
        self.level = lb.value_to_core('level', level)
        self.update_core_levels()
        
    def get_level (self):
        return lb.value_to_string('level', self.level)

    def set_color (self, color):
        self.color = lb.value_to_core('color', color)
        self.update_core_levels()
        
    def get_color (self):
        return lb.value_to_string('color', self.color)

    def get_attribute (self, name):
        if name == 'level': return self.get_level()
        if name == 'color': return self.get_color()
        raise AttributeError, name
    
    def set_attribute (self, name, arg):
        if name == 'level': return self.set_level(arg)
        if name == 'color': return self.set_color(arg)
        raise AttributeError, name
        
    def calculate_core_levels(self, level, color):
        lr = level[0]/100.0
        (r,g,b) = (color[0]*lr, color[1]*lr, color[2]*lr)
        (r,g,b) = map (lambda x: lb.value_to_string('level', x), (r,g,b))
        return (r,g,b)

    def update_core_levels(self):
        (r,g,b) = self.calculate_core_levels(self.level, self.color)
        lb.instrument[self.red_name].set_level(r)
        lb.instrument[self.green_name].set_level(g)
        lb.instrument[self.blue_name].set_level(b)
        
    def to_core_InstAttrs (self, attr_dict):
        """ Used by Cues to create a core cue.  But note how easily it
        can be overridden to return a list of several InstAttrs,
        so that you can have a kind of Meta-Instrument that controls more
        than one actual instrument. """

        try:
            (rl,gl,bl) = self.calculate_core_levels(
                lb.value_to_core('level', attr_dict['level']),
                lb.value_to_core('color', attr_dict['color']))
        except:
            return []
        
        ri = lb.instrument[self.red_name].to_core_InstAttrs({'level': rl})
        gi = lb.instrument[self.green_name].to_core_InstAttrs({'level': gl})
        bi = lb.instrument[self.blue_name].to_core_InstAttrs({'level': bl})

        return ri + gi + bi
    
