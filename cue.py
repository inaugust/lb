from xmllib import XMLParser
from os import path
import string
import lightboard
from Numeric import *
from ExpatXMLParser import ExpatXMLParser

def initialize(lb):
    lb.cue={}
    try:
        f=open(path.join(lb.datapath, 'cues'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()
        
def shutdown():
    pass


class parser(ExpatXMLParser):
    def start_instrument (self, attrs):
        d={}
        for key, value in attrs.items():
            if key == "name": continue
            d[key]=value
        self.cue.instrument[attrs['name']]=d

    def start_cue (self, attrs):
        self.cue=cue(attrs['name'])

    def end_cue (self):
        self.cue._init()
        lb.cue[self.cue.name]=self.cue

class cue:

    def __init__(self, name):
        self.instrument={}
        self.name=name
        self.matrix=lb.newmatrix()
        
    def _init(self):
        "recalculates matrix"
        self.matrix=lb.newmatrix()
        for (iname, d) in self.instrument.items():
            ins=lb.instrument[iname]
            self.matrix=self.matrix+ins.get_matrix(d)
    
