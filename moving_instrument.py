# this class is only a template for moving instruments of different brands
# it should not be used in an actual installation
# instead, edit it to create a new module

from xmllib import XMLParser
from os import path
import lightboard
import instrument

def initialize(lb):
    if not hasattr(lb, 'instrument'):
        lb.instrument={}
    try:
        f=open(path.join(lb.datapath, 'moving_instruments'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())
        
def shutdown():
    pass


class parser(XMLParser):
    def start_instrument (self, attrs):
        lb.instrument[attrs['name']]=moving_instrument(attrs['name'],
                                                       int(attrs['bank']),
                                                       int(attrs['dimmer']))

class moving_instrument(instrument.instrument):

    attributes=('level', 'x', 'y')
    
    def __init__(self, name, bank, number):
        instrument.__init__(self, name, bank, number)
        current_x=0
        current_y=0
        self.x_dimmer=lb.dimmer_bank[self.bank][self.number+1]
        self.y_dimmer=lb.dimmer_bank[self.bank][self.number+2]

#private

    def set_current_attribute (self, attr, level):
        #meant to be overridden when new keys are defined:
        if (attr=='level'):
            self.current_level=level
            self.dimmer.set_level(level)
        if (attr=='x'):
            self.current_x=level
            self.x_dimmer.set_level(level)
        if (attr=='y'):
            self.current_y=level
            self.y_dimmer.set_level(level)
