from threading import *
from xmllib import XMLParser
from os import path
import string, cStringIO
from ExpatXMLParser import ExpatXMLParser
from gtk import *

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
        self.procedure=procedure (attrs['name'], attrs['args'])

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
        self.procedure=None

    def handle_data (self, data):
        if (not self.in_procedures): return
        if (hasattr(self,'procedure') and self.procedure):
            self.procedure.proc=self.procedure.proc+data
        
class procedure:

    def __init__(self, name, args):
        self.name = name
        if string.strip(args)=='':
            self.args=[]
        else:
            self.args = map(string.strip, string.split(args, ','))
        self.proc = ''
        lb.procedure[self.name]=self
        
    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        args = ''
        for a in self.args:
            args=args+a+', '
        args=args[:-2]
        s = s + sp + '<procedure name="%s" args="%s">\n' % (self.name, args)
        s = s +self.proc + "\n"
        s = s + sp + '</procedure>\n'
        return s

    def argument_widget(self):
        l = len(self.args)
        table = GtkTable(rows=l, cols=2)
        print l, self.args
        for x in range(0,l):
            label = GtkLabel(self.args[x])
            label.set_alignment(1.0, 0.5)
            label.show()
            table.attach(label, 0, 1, x, x+1, xoptions=FILL, yoptions=0)
            entry = GtkEntry()
            entry.show_all()
            align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
            align.add(entry)
            align.show()
            table.attach(align, 1, 2, x, x+1, xoptions=FILL, yoptions=0)
        table.show_all()
        return table
