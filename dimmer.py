from threading import *
from xmllib import XMLParser
from os import path
import time
from Numeric import *
from xml.parsers import expat
from ExpatXMLParser import ExpatXMLParser

def make_level (level):
    if (type(level)==type(1)):
        return level
    if (type(level)==type(1.0)):
        return int(level)
    level=str(level)
    if (level[-1]=='%'):
        level=int((float(level[:-1])/100.0)*255.0)
    else:
        level=int(level)
    return level

def newmatrix():
    m=zeros(lb.num_dimmers, UnsignedInt8)
    #m.savespace(1)
    return m

def get_sources (typ='min'):
    if typ=='min':
        return lb.min_source
    if typ=='max':
        return lb.max_source
    if typ=='add':
        return lb.add_source
    if typ=='sub':
        return lb.sub_source
    if typ=='capture':
        return lb.capture_source
    if typ=='scale':
        return lb.scale_source
    if typ=='blackout':
        return lb.blackout_source

def update_dimmers ():
    matrix = lb.newmatrix()
    if (len(lb.blackout_source)==0):
        for m in lb.min_source.values():
            matrix=maximum(matrix,m)
        for m in lb.max_source.values():
            matrix=minimum(matrix,m)
        for m in lb.add_source.values():
            matrix=matrix+m
        for m in lb.sub_source.values():
            matrix=matrix-m
        for m in lb.capture_source.values():
            matrix=choose(greater(m, 0), (matrix, m))
        for m in lb.scale_source.values():
            matrix=matrix*m

    # Self set dimmers
    matrix=choose(greater(lb.dimmer_matrix, 0), (matrix, lb.dimmer_matrix))
    
    lb.dimmer_lock.acquire()
    for (start, end, fh) in lb.dimmer_device:
        fh.seek(start)
        fh.write(matrix[start:end].tostring())
        fh.flush()
        #for x in matrix[start:end]:
        #    if x>255:
        #        None.bah()
    lb.dimmer_lock.release()
    lb.foo_dimmer_0.write(str(time.time()) + ' ' + str(matrix[0])+"\n")
    lb.foo_dimmer_1.write(str(time.time()) + ' ' + str(matrix[1])+"\n")
    #for x in lb.dimmer:
    #    x.set_level_real(matrix[x.number])

def initialize(lb):
    lb.dimmer=[]
    lb.dimmer_device=[]
    lb.num_dimmers=0

    lb.min_source={}       #minimum values (typical)
    lb.max_source={}       #maximum values
    lb.add_source={}       #additive values
    lb.sub_source={}       #subtractive values (weird)
    lb.capture_source={}   #captured values
    lb.scale_source={}     #scale values (grand master)
    lb.blackout_source={}  #blackouts (boolean, not matrix)
    
    f=open(path.join(lb.datapath, 'dimmers'))
    p=parser()
    p.Parse(f.read())
    p.close()
    lb.add_signal ('Dimmer Set Level', dimmer.set_level_real)
    lb.dimmer_range=255
    lb.make_level=make_level
    lb.update_dimmers=update_dimmers
    lb.get_sources=get_sources
    lb.newmatrix=newmatrix
    lb.dimmer_matrix=lb.newmatrix()
    lb.dimmer_file = open('/dev/dmx', 'w')
    lb.dimmer_lock=Lock()

def shutdown():
    lb.foo_dimmer_0.close()
    lb.foo_dimmer_1.close()
    for (start, end, fh) in lb.dimmer_device:
        fh.close()
    #for d in lb.dimmer:
    #    if d.fd:
    #        d.fd.close()

class parser(ExpatXMLParser):

    def start_dimmerbank (self, attrs):
        start=lb.num_dimmers
        end=start+lb.num_dimmers
        dev=attrs['dev']
        for x in range(0, int(attrs['dimmers'])):
            lb.dimmer.append (dimmer(start+x))
        lb.num_dimmers=lb.num_dimmers+int(attrs['dimmers'])
        fh = open(dev, 'w')
        r=(start, end, fh)
        lb.dimmer_device.append(r)

class dimmer:

    current_level=0
    max_level=255
    bank=-1
    number=-1
    
    def __init__(self, number):
        self.number=number
        if number==0:
            fn="/tmp/dimmer/"+str(number)
            lb.foo_dimmer_0=open(fn, "w")
        if number==1:
            fn="/tmp/dimmer/"+str(number)
            lb.foo_dimmer_1=open(fn, "w")
        #if number<50:
        #    fn="/tmp/dimmer/"+str(number)
        #    print fn
        #    self.fd=open(fn, "w")
        #else:
        #    self.fd=None
#public

    def set_level(self, level, immediately=1):
        #lb.send_signal('Dimmer Set Level', itself=self, level=level)
        self.set_level_real(level, immediately)
        
    def make_level (self, level):
        return make_level(level)

#private

    def set_level_real(self, level, immediately=1):
        if (level<0): level=0
        if (level>self.max_level): level=self.max_level
        self.current_level=level
        #print args['level']
        #update hardware
        #print 'dim', self.number, level
        if (immediately):
            lb.dimmer_lock.acquire()
            lb.dimmer_file.seek(self.number)
            lb.dimmer_file.write(chr(level))
            lb.dimmer_file.flush()
	    #print 'dimmer ', self.number, '@ ', level
            lb.dimmer_lock.release()
        lb.dimmer_matrix[self.number]=level
        #if self.number<50:
        #    self.fd.write(str(time.time()) + ' ' + str(level)+"\n")






