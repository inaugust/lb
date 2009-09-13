# A subclass of instrument to demonstrate it's meta-ness.
# It's designed to represent three instruments, gelled RGB.
# When you set this instrument's color and level, it will set the
# appropriate levels of the other instruments.

from os import path
import lightboard
import time
import attribute_widgets
import instrument

from xml.parsers import expat
from ExpatXMLParser import ExpatXMLParser, DOMNode
from idl import LB

def initialize():
    lb.instrument_module_info['Color Mixer Instrument'] = instrument_info

def reset():
    pass

def shutdown():
    pass


def load_clump(tree, group = None):
    for ins in tree.find("color_mixer_instrument"):
        i=ColorMixerInstrument(ins.attrs['name'], ins.attrs['red'],
                               ins.attrs['green'], ins.attrs['blue'], group)

def load(tree):
    for section in tree.find("instruments"):
        load_clump(section)
        for group in section.find("group"):
            load_clump(group, group.attrs['name'])
                         
def save():
    # instrument's routine is sufficient
    pass

        
class ColorMixerInstrument(instrument.Instrument):

    attributes=('level','color',)
    module='color_mixer_instrument'

    def __init__(self, name, red, green, blue, group = None):
        self.parent = None
        self.group = group
        self.hidden = 0
        self.name=name
        self.red_name = red
        self.green_name = green
        self.blue_name = blue
        self.level = [0.0]
        self.color = [0.0, 0.0, 0.0]

        if group is not None:
            if not lb.instrument_group.has_key(group):
                lb.instrument_group[group]={}
            lb.instrument_group[group][self.name]=self
        else:
            lb.instrument_group[None][self.name]=self

        lb.instrument[self.name]=self

    #public

    def to_tree(self):
        instrument = DOMNode(self.module, {'name':self.name,
                                           'red':self.red_name,
                                           'green':self.green_name,
                                           'blue':self.blue_name})
        return instrument

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
    
class InstrumentInfo:
    container = 1
    module = 'color_mixer_instrument'
    clazz = ColorMixerInstrument

    def load(self, tree):
        load(tree)
    
    def get_arguments(self, ins):
        dict = {'name': ['', ''],
                'red': ['red', ''],
                'green': ['green', ''],
                'blue': ['blue', '']
                }
        for name, value in dict.items():
            if ins.attrs.has_key(name):
                dict[name][0]=ins.attrs[name]
        return dict

    def get_arguments_for_children(self, ins):
        return {}

instrument_info = InstrumentInfo()
