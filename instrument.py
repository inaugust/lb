from xmllib import XMLParser
from os import path
import lightboard


#types:
# max
# min
# add
# sub
# capture
# blackout


def initialize(lb):
    lb.instrument={}
    try:
        f=open(path.join(lb.datapath, 'instruments'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())
    lb.add_signal ('Instrument Set Attribute', instrument.set_attribute_real_vf)

def shutdown():
    pass

class parser(XMLParser):

    def start_instrument (self, attrs):
        lb.instrument[attrs['name']]=instrument(attrs['name'],
                                                int(attrs['bank']),
                                                int(attrs['dimmer']))


class instrument:

    attributes=('level',)

    def __init__(self, name, bank, number):
        self.name=name
        self.bank=bank
        self.number=number
        self.sources={}
        self.current_level=0
        self.dimmer=lb.dimmer_bank[self.bank][self.number]

#public

    def set_attribute(self, attribute, value, source, typ='min'):
        lb.send_signal('Instrument Set Attribute', itself=self,
                       attribute=attribute, value=value, source=source,
                       typ=typ)

    def make_level(self, level):
        return self.dimmer.make_level(level)

    def get_attributes(self):
        return self.attributes

#private

    def set_attribute_real_vf(self, args):
        self.set_attribute_real(args)
        
    def set_attribute_real(self, args):
        attribute=str(args['attribute'])
        value=str(args['value'])
        typ=args['typ']
        source=args['source']
        
        if (attribute=='level'):
            self.do_set_level (value, typ, sourc)
            
    def do_set_level (self, value, typ, source):
        level=self.dimmer.make_level(value)
        
        if (typ=='min' and level==0):
            if (self.sources.has_key(source) and
                self.sources[source].has_key('level')):
                del self.sources[source]['level']
        else:
            if (not self.sources.has_key(source)):
                self.sources[source]={}
            self.sources[source]['level']=(level, typ)
        self.update_level()
        
    def update_level(self):
        min_of_maxs=self.dimmer.max_level
        max_of_mins=0
        total_adds=0
        total_subs=0
        capture=None
        blackout=None
        
        for source in self.sources.values():
            (v,typ) = source['level']
            if typ=='max':
                if (min_of_maxs>v):
                    min_of_maxs=v
            if typ=='min':
                if (max_of_mins<v):
                    max_of_mins=v
            if typ=='add':
                total_adds=total_adds+v
            if typ=='sub':
                total_subs=total_subs+v
            if typ=='capture':
                capture=v
            if typ=='blackout':
                blackout=0

        if (blackout!=None):
            level=0
        elif (capture!=None):
            level=capture
        else:
            level=min_of_maxs
            if (level>max_of_mins):
                level=max_of_mins
            level=level+total_adds
            level=level-total_subs

        self.current_level=level
        self.dimmer.set_level(level)
