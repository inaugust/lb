from xmllib import XMLParser
from os import path
import string
import lightboard

def initialize(lb):
    lb.cue={}
    try:
        f=open(path.join(lb.datapath, 'cues'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())
    
def shutdown():
    pass


class parser(XMLParser):

    def start_instrument (self, attrs):
        d={}
        d['level']=lb.instrument[attrs['name']].make_level(attrs['level'])
        self.cue.instrument[attrs['name']]=d

    def start_cue (self, attrs):
        self.cue=cue(attrs['name'])

    def end_cue (self):
        lb.cue[self.cue.name]=self.cue

class cue:

    def __init__(self, name):
        self.instrument={}
        self.name=name
