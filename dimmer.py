from threading import *
from xmllib import XMLParser
from os import path
import time

def make_level (level):
    level=str(level)
    if (level[-1]=='%'):
        level=int((float(level[:-1])/100.0)*255.0)
    else:
        level=int(level)
    return level

def initialize(lb):
    lb.dimmer_bank=[]
    f=open(path.join(lb.datapath, 'dimmers'))
    p=parser()
    p.feed(f.read())
    lb.add_signal ('Dimmer Set Level', dimmer.set_level_real)
    lb.dimmer_range=255
    lb.make_level=make_level
    lb.dimmer_file = open('/dev/dmx', 'w')
    lb.dimmer_lock=Lock()

def shutdown():
    for d in lb.dimmer_bank[0]:
        if d.fd:
            d.fd.close()

class parser(XMLParser):

    def start_dimmerbank (self, attrs):
        bank=len(lb.dimmer_bank)
        dimmers=[]
        for x in range (0, int(attrs['dimmers'])):
            dimmers.append (dimmer(bank, x))
        lb.dimmer_bank.append(dimmers)

class dimmer:

    current_level=0
    max_level=255
    bank=-1
    number=-1
    
    def __init__(self, bank, number):
        self.bank=bank
        self.number=number
        #if number<50:
        #    fn="/tmp/dimmer/"+str(bank)+"-"+str(number)
        #    print fn
        #    self.fd=open(fn, "w")
        #else:
        self.fd=None
#public

    def set_level(self, level):
        #lb.send_signal('Dimmer Set Level', itself=self, level=level)
        self.set_level_real({'level':level})
        
    def make_level (self, level):
        return make_level(level)

#private

    def set_level_real(self, args):
        level=args['level']
        if (level<0): level=0
        if (level>self.max_level): level=self.max_level
        self.current_level=level
        #print args['level']
        #update hardware
        #print 'dim', self.number, level
	lb.dimmer_lock.acquire()
        lb.dimmer_file.seek(self.number)
        lb.dimmer_file.write(chr(level))
        lb.dimmer_file.flush()
	#print 'dimmer ', self.number, '@ ', level
        lb.dimmer_lock.release()
        #if self.number<50:
        #    self.fd.write(str(time.time()) + ' ' + str(level)+"\n")






