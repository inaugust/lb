# this class is only a template for moving instruments of different brands
# it should not be used in an actual installation
# instead, edit it to create a new module

from xmllib import XMLParser
from os import path
import lightboard
from instrument import instrument
import string
import re
from math import *

RE_FT = re.compile ("[-+]?(\d*.\d+|\d+)\s*ft", re.I)
RE_IN = re.compile ("[-+]?(\d*.\d+|\d+)\s*in", re.I)
RE_M = re.compile ("[-+]?(\d*.\d+|\d+)\s*m", re.I)
RE_CM = re.compile ("[-+]?(\d*.\d+|\d+)\s*cm", re.I)

def len_to_ft(l):
    m=RE_FT.match(l)
    if m:
        return float(m.group(1))
    m=RE_IN.match(l)
    if m:
        return float(m.group(1))/12.0
    m=RE_M.match(l)
    if m:
        return float(m.group(1))/3.2808399
    m=RE_CM.match(l)
    if m:
        return float(m.group(1))/30.48
    # error: can't convert

def initialize(lb):
    if not hasattr(lb, 'instrument'):
        lb.instrument={}
    try:
        f=open(path.join(lb.datapath, 'instruments'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())
        
def shutdown():
    pass


class parser(XMLParser):
    def start_moving_instrument (self, attrs):
        lb.instrument[attrs['name']]=moving_instrument(attrs['name'],
                                                       int(attrs['bank']),
                                                       int(attrs['dimmer']))

class moving_instrument(instrument):

    attributes=('level', 'location')

    # thetadelta = beam change in x direction in degrees per dmx unit
    theta_delta = 0.05

    # phidelta   = beam change in y direction in degrees per dmx unit
    phi_delta = 0.05
    
    def __init__(self, name, bank, number):
        instrument.__init__(self, name, bank, number)
        self.current_location = (0.0, 0.0, 0.0)
        
        # xyz location of instrument, in feet
        self.x_location = 0.0
        self.y_location = -20.0
        self.z_location = 20.0

        # corrections, in degrees, for angular mounting of instrument
        self.theta_correction = 0.0
        self.phi_correction = 0.0

        #subclass sets these
        self.x_dimmer=lb.dimmer_bank[self.bank][self.number+1]
        self.y_dimmer=lb.dimmer_bank[self.bank][self.number+2]

#private
    def set_attribute_real(self, args):
        attribute=str(args['attribute'])
        value=str(args['value'])
        typ=args['typ']
        source=args['source']
        
        if (attribute=='level'):
            instrument.do_set_level (self, value, typ, source)
        if (attribute=='location'):
            self.do_set_location (value, typ, source)

    def xyz_to_xy (self, value):
        (tx, ty, tz) = string.split(value[1:-1], ',')
        (tx, ty, tz) = map (string.strip, (tx, ty, tz))
        # do unit conversion here.  end up with feet
        (tx, ty, tz) = map (len_to_ft, (tx, ty, tz))
        # i is the instrument location
        ix = self.x_location
        iy = self.y_location
        iz = self.z_location
        # b is the instrument projected onto the xy plane
        bx=self.x_location
        by=self.y_location
        bz=0.0
        # p is target point projected onto the yz plane
        px=0.0
        py=ty
        pz=tz
        sidea = sqrt( ((ix-tx)**2) + ((iy-ty)**2) + ((iz-tz)**2) )
        sideb = sqrt( ((ix-bx)**2) + ((iy-by)**2) + ((iz-bz)**2) )
        sidec = sqrt( ((tx-bx)**2) + ((ty-by)**2) + ((tz-bz)**2) )
        phi=acos( (sidea**2 + sideb**2 - sidec**2)/(2*sidea*sideb) )
        phi=phi + self.phi_correction
        
        sideb = sqrt( ((ix-px)**2) + ((iy-py)**2) + ((iz-pz)**2) )
        sidec = sqrt( ((tx-px)**2) + ((ty-py)**2) + ((tz-pz)**2) )
        theta=acos( (sidea**2 + sideb**2 - sidec**2)/(2*sidea*sideb) )
        theta=theta+self.theta_correction

        ylevel=phi/self.phi_delta
        xlevel=theta/self.theta_delta
        return (xlevel, ylevel)
        
    def do_set_location (self, value, typ, source):
        if (typ=='min' and value==''):
            if (self.sources.has_key(source) and
                self.sources[source].has_key('location')):
                del self.sources[source]['location']
        else:
            if (not self.sources.has_key(source)):
                self.sources[source]={}
            self.sources[source]['location']=(value, typ)
        self.update_location()
        
    def update_location(self):
        location=''
        capture=None
        blackout=None
        
        for source in self.sources.values():
            (v,typ) = source['location']
            if typ=='capture':
                capture=v
            elif typ=='blackout':
                blackout=0
            else:
                location=v
                
        if (blackout!=None):
            location='(0ft, 0ft, 0ft)'
        elif (capture!=None):
            location=capture

        self.current_location=location
        (x, y)=self.xyz_to_xy (location)
        print 'update location', x, y
        self.x_dimmer.set_level(int(x))
        self.y_dimmer.set_level(int(y))

