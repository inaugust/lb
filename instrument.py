from xmllib import XMLParser
from os import path
import lightboard
import time
from Numeric import *

from xml.parsers import expat
from ExpatXMLParser import ExpatXMLParser

#types:
# max
# min
# add
# sub
# capture
# scale
# blackout


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
    lb.add_signal ('Instrument Set Attribute', instrument.set_attribute_real_vf)

def shutdown():
    pass

class parser(ExpatXMLParser):
    def start_instrument (self, attrs):
        lb.instrument[attrs['name']]=instrument(attrs['name'],
                                                int(attrs['dimmer']))

class instrument:

    attributes=('level',)

    def __init__(self, name, dimmer_number):
        self.name=name
        self.dimmer_number=dimmer_number
        self.sources={}
        self.level=0
        self.dimmer=lb.dimmer[self.dimmer_number]

    #public

    def set_attribute(self, attribute, value, source=None, typ='min',
                      immediately=1):
        #print 'set!'
        #lb.send_signal('Instrument Set Attribute', itself=self,
        #               attribute=attribute, value=value, source=source,
        #               typ=typ, immediately=immediately)
        self.set_attribute_real({'attribute':attribute,
                                 'value':value,
                                 'source':source,
                                 'typ':typ,
                                 'immediately':immediately})

    def make_level(self, level):
        return self.dimmer.make_level(level)

    def get_attributes(self):
        return self.attributes

    def get_matrix(self, dict):
        matrix=lb.newmatrix()
        for (attr, val) in dict.items():
            if attr=='level':
                matrix[self.dimmer_number]=self.make_level(val)
        return matrix

    def get_path(self):
        return '/instrument/'+self.name

    def get_attribute(self, attribute=None):
        if attribute=='level':
            return self.level

#private

    def set_attribute_real_vf(self, args):
        # only needed for recieving signals
        self.set_attribute_real(args)
        
    def set_attribute_real(self, args):
        if (args['attribute']=='level'):
            self.do_set_level (args['value'], args['typ'], args['source'],
                               args['immediately'])

    def do_set_level (self, value, typ, source, immediately):
        self.level=value
        level=self.make_level(value)
        self.dimmer.set_level(level, immediately) 
        
    def __repr__(self):
        r='<%s "%s"' % (self.__class__.__name__, self.name)
        for x in self.attributes:
            r=r+' %s="%s"' % (x, getattr(self, x))
        r=r+'>'
        return r


# Attic:
#         dict = lb.get_sources(typ)
#         m = self.get_matrix({'level': value})
#         try:
#             matrix=dict[source]
#         except:
#             matrix=lb.newmatrix()
#         matrix=choose(greater(m, 0), (matrix, m))        
#         dict[source]=matrix
#         lb.update_dimmers()
