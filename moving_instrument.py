# base class for moving lights

from xmllib import XMLParser
from os import path
import lightboard
from instrument import instrument
import string
import re
from math import *
from ExpatXMLParser import ExpatXMLParser

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
    lb.len_to_ft=len_to_ft
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
    def start_moving_instrument (self, attrs):
        name = attrs['name']
        dimmer = int(attrs['dimmer'])
        if attrs.has_key('xloc'):  x = len_to_ft (attrs['xloc'])
        else: x=0
        if attrs.has_key('yloc'):  y = len_to_ft (attrs['yloc'])
        else: y=0
        if attrs.has_key('zloc'):  z = len_to_ft (attrs['zloc'])
        else: z=0
        if attrs.has_key('theta'):  theta = float (attrs['theta'])
        else: theta=0
        if attrs.has_key('phi'):  phi = float (attrs['phi'])
        else: phi=0
        
        lb.instrument[attrs['name']]=moving_instrument(name, dimmer,
                                                       x, y, z, theta, phi)
                                                       

class moving_instrument(instrument):

    attributes=('level', 'target')

    # thetadelta = beam change in x direction in degrees per dmx unit
    theta_delta = 0.05

    # phidelta   = beam change in y direction in degrees per dmx unit
    phi_delta = 0.05
    
    def __init__(self, name, dimmer_number, x, y, z, theta, phi):
        instrument.__init__(self, name, dimmer_number)
        self.target = "(0ft, 0ft, 0ft)"
        self.location = (0.0, 0.0, 0.0)
        
        # xyz location of instrument, in feet
        self.x_location = x
        self.y_location = y
        self.z_location = z

        # corrections, in degrees, for angular mounting of instrument
        self.theta_correction = theta
        self.phi_correction = phi

        #subclass sets these
        self.lamp_dimmer_number=self.dimmer_number
        self.x_dimmer_number=self.dimmer_number+1
        self.y_dimmer_number=self.dimmer_number+2

        self.lamp_dimmer=lb.dimmer[self.lamp_dimmer_number]
        self.x_dimmer=lb.dimmer[self.x_dimmer_number]
        self.y_dimmer=lb.dimmer[self.y_dimmer_number]

    def get_matrix(self, dict):
        matrix=lb.newmatrix()
        for (attr, val) in dict.items():
            if attr=='level':
                matrix[self.lamp_dimmer_number]=self.make_level(val)
        return matrix

#private
    def set_attribute_real(self, args):
        attribute=args['attribute']
        value=args['value']
        typ=args['typ']
        source=args['source']
        immediately=args['immediately']
        
        if (attribute=='level'):
            self.do_set_level (value, typ, source, immediately)
        if (attribute=='target'):
            self.do_set_target (value, typ, source, immediately)

    def xyz_to_xy (self, value):
        if (type(value)==type('string')):
            (tx, ty, tz) = string.split(value[1:-1], ',')
            (tx, ty, tz) = map (string.strip, (tx, ty, tz))
            # do unit conversion here.  end up with feet
            (tx, ty, tz) = map (len_to_ft, (tx, ty, tz))
        else:
            (tx, ty, tz) = value
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
        
    def do_set_target (self, value, typ, source, immediately):
        self.target=value
        (x, y)=self.xyz_to_xy (value)
        self.x_dimmer.set_level(x, immediately)
        self.y_dimmer.set_level(y, immediately)


# Attic:
#             if attr=='location':
#                 (x, y)=self.xyz_to_xy (val)
#                 matrix[self.x_dimmer_number]=x
#                 matrix[self.y_dimmer_number]=y
