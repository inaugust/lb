from threading import *
from xmllib import XMLParser
from os import path
import string, cStringIO

def initialize(lb):
    lb.procedure={}
    try:
        f=open(path.join(lb.datapath, 'procedures'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())

def shutdown():
    pass

class parser(XMLParser):

    def start_procedure (self, attrs):
        self.procedure=procedure (attrs['name'])

    def end_procedure (self):
        sio=cStringIO.StringIO(self.procedure.proc)
        proc=''
        while (1):
            line=sio.readline()
            if not line: break
            if string.strip(line)=='':
                proc=proc+'\n'
            else:
                proc=proc+line
        self.procedure.comp=compile(proc, self.procedure.name,'exec')
        lb.procedure[self.procedure.name]=self.procedure
        self.procedure=None

    def handle_data (self, data):
        if (hasattr(self,'procedure') and self.procedure):
            self.procedure.proc=self.procedure.proc+data
        
class procedure:

    def __init__(self, name):
        self.name=name
        self.proc=''
        
