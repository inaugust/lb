from threading import *
from xmllib import XMLParser
from os import path
import string, cStringIO
from ExpatXMLParser import ExpatXMLParser

def initialize():
    reset()

def reset():
    lb.procedure={}
    
def shutdown():
    pass

def load(data):
    p=parser()
    p.Parse(data)
    p.close()

def save():
    s="<procedures>\n\n"
    for c in lb.procedure.values():
        s=s+c.to_xml(1)
    s=s+"</procedures>\n"
    return s

class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_procedures=0
        
    def start_procedures (self, attrs):
        self.in_procedures=1

    def end_procedures (self):
        self.in_procedures=0

    def start_procedure (self, attrs):
        if (not self.in_procedures): return
        self.procedure=procedure (attrs['name'])

    def end_procedure (self):
        if (not self.in_procedures): return
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
        if (not self.in_procedures): return
        if (hasattr(self,'procedure') and self.procedure):
            self.procedure.proc=self.procedure.proc+data
        
class procedure:

    def __init__(self, name):
        self.name=name
        self.proc=''
        
    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s = s + sp + '<procedure name="%s">\n' % self.name
        s = s +self.proc + "\n"
        s = s + sp + '</procedure>\n'
        return s
