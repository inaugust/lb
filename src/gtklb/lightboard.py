import __main__
import sys
import operator
from threading import *
import string
import time
from gtk import *
from libglade import *
import GDK
from rexec import RExec
import __builtin__
import __main__
from completion import completion
from ExpatXMLParser import ExpatXMLParser, DOMNode, reverse_translate_references
import attribute_widgets

import os
os.environ['IDLPATH']=os.environ.get('IDLPATH','')+':/usr/share/idl:/usr/local/share/idl:omniorb-core'

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

import string

COPYRIGHT="Copyright 2001 In August Productions, INC."

class parser(ExpatXMLParser):

    def start_show (self, attrs):
        self.in_show=1
        self.name=attrs['name']

    def end_show (self):
        self.in_show=0

    def get_name (self):
        return self.name


class TreeParser (ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.tree = None
        self.stack = []

    def unknown_starttag (self, name, attrs):
        n = DOMNode(name, attrs)
        if len(self.stack) == 0:
            self.tree = n
        else:
            self.stack[-1].append(n)
        self.stack.append(n)

    def unknown_endtag (self, name):        
        self.stack.pop()

    def handle_data (self, data):
        self.stack[-1].add_data(data)

class TreeWriter:
    def __init__ (self, level=0):
        self.s = ''
        self.ilevel=level

    def get_string (self):
        return self.s
    
    def indent(self):
        return ' '*self.ilevel
        
    def write(self, tree):
        self.s=self.s+self.indent()+'<'+tree.tag+' '
        for a,v in tree.attrs.items():
            self.s = self.s + a + '="' + str(v) + '" '
        if len(tree.children) == 0 and len(tree.data) == 0:
            self.s = self.s + '/>\n'
        else:
            self.s = self.s + '>\n'
            self.ilevel = self.ilevel + 2
            for n in tree.children:
                self.write(n)
            if (len (tree.data)):
                self.s = self.s + self.indent() + reverse_translate_references(tree.data) + "\n"
            self.ilevel = self.ilevel - 2
            self.s=self.s+self.indent()+'</'+tree.tag+'>\n'
    

class lightboard(completion, LB__POA.Client):

    _signals={}
    _event_queue=[]
    _libraries=[]

    _queue_lock=None
    _queue_count=None

    _terminated=0

    def __init__(self, myname):
        completion.__init__(self, {'lb':self})
        self.show='unnamed'
        self.name=myname
        self.datafile=None
        __builtins__['lb']=self

        self.orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        self.poa = self.orb.resolve_initial_references("RootPOA")
        nsi=self.orb.resolve_initial_references("NameService")
        ns = nsi._narrow(CosNaming.NamingContext)
        self.root_naming = ns

        self.do_bindings()

        self.poa._get_the_POAManager().activate()
        t=Thread (target=self.orb.run)
        t.start()

        self.check_cores()
        
        self.create_window()

    def do_bindings(self,client=0):
        x=CosNaming.NameComponent("shows","")
        try:
            o = self.root_naming.resolve([x])
        except:
            o = self.root_naming.bind_new_context([x])

        x=CosNaming.NameComponent(self.show,"")
        try:
            o = o.resolve([x])
        except:
            o = o.bind_new_context([x])

        x=CosNaming.NameComponent("clients","")

        try:
            client_ctx = o.resolve([x])
        except:
            client_ctx = o.bind_new_context([x])

        x=CosNaming.NameComponent(self.name, "Client")

        try:
            i = client_ctx.rebind([x], self._this())
        except:
            
            print 'Unable to bind client'

        x=CosNaming.NameComponent("instruments","")

        try:
            ins_ctx = o.resolve([x])
        except:

            ins_ctx = o.bind_new_context([x])

        x=CosNaming.NameComponent("faders","")

        try:
            fad_ctx = o.resolve([x])
        except:

            fad_ctx = o.bind_new_context([x])

        self.instrument_context = ins_ctx
        self.fader_context = fad_ctx
        self.client_context = client_ctx

    def undo_bindings(self):
        x=CosNaming.NameComponent(self.name, "Client")
        self.client_context.unbind([x])

    def check_cores(self):
        self.core_names=[]
        x=CosNaming.NameComponent("lightboards","")
        o = self.root_naming.resolve([x])
        (foo,iterator) = o.list(0)
        while 1:
            (c,b)=iterator.next_one()
            if not c:
                break
            self.core_names.append(str(b.binding_name[0].id))
        
    def run(self):
        self.write ("GTK Lightboard client\n")
        self.write (COPYRIGHT+"\n")
        self.write ("Working in show: %s\n" % self.show)

        names=''
        for name in self.core_names:
            names=names+" "+name
        
        self.write ("Connected to core dimmer controlers: %s \n" % names)
        self.write ("Ready.\n")
        
    def load_libraries(self, libs):
        for lib in libs:
            print "Loading library: " + lib
            l=__import__(lib, globals(), locals(), [])
            l.initialize()
            self._libraries.append(l)

    def load_show(self, datafile):
        self.write("Loading show " + datafile + "\n")

        self.datafile = datafile
        f=open(datafile)
        data = f.read()

        p=parser()
        p.Parse(data)
        p.close()
        self.undo_bindings()        
        self.name = str(p.get_name())
        self.do_bindings()

        p=TreeParser()
        p.Parse(data)
        p.close()
        tree = p.tree
        
        for lib in self._libraries:
            lib.load(tree)
        self.write("Now working in show " + self.show +"\n")

    def save_show(self, datafile=None):
        if datafile is not None:
            self.datafile = datafile
        else:
            datafile = self.datafile

        tree = DOMNode('show', {'name':self.show})

        for lib in self._libraries:
            tree.append (lib.save())
            
        writer = TreeWriter()
        writer.write(tree)
        s = writer.get_string()
        f=open(datafile, "w")
        f.write(s)

    def change_show(self, newname, clear=0):
        self.datafile=None
        self.undo_bindings()
        self.show = newname
        self.do_bindings()
        if (clear):
            for lib in self._libraries:
                lib.reset()
        else:
            tree = DOMNode('show', {'name':self.show})            
            for lib in self._libraries:
                tree.append (lib.save())
            for lib in self._libraries:                    
                lib.load(tree)
        self.write("Now working in show " + self.show +"\n")
        
    def exit (self):
        for lib in self._libraries:
            lib.shutdown()
        sys.exit(0)

    def get_instrument(self, name):
        try:
            x=CosNaming.NameComponent(name, "Instrument")
            i = self.instrument_context.resolve([x])
            return i
        except:
            return None

    def get_fader(self, name):
        try:
            x=CosNaming.NameComponent(name, "Fader")
            i = self.fader_context.resolve([x])
            return i
        except:
            return None

    def get_core(self, name):
        x=CosNaming.NameComponent("lightboards", "")
        o = self.root_naming.resolve([x])
        x=CosNaming.NameComponent(name, "")
        print name, x
        o = o.resolve([x])
        x=CosNaming.NameComponent("lb", "Lightboard")
        o = o.resolve([x])
        return o

    def sort_by_attr(self, seq, attr):
        intermed = map(None, map(getattr, seq, (attr,)*len(seq)),
                       xrange(len(seq)), seq)
        intermed.sort()
        return map(operator.getitem, intermed, (-1,) * len(intermed))

    def core_attr_id (self, name):
        return attribute_widgets.attribute_mapping[name][0]

    def attr_widget (self, name):
        return attribute_widgets.attribute_mapping[name][1]
            
    def value_to_string(self, name, value):
        return attribute_widgets.attribute_mapping[name][3](value)

    def value_to_core(self, name, value):
        return attribute_widgets.attribute_mapping[name][2](value)

    def create_window(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "main")

            dic = {"on_new_activate": self.on_new_activate,
                   "on_open_activate": self.on_open_activate,
                   "on_save_activate": self.on_save_activate,
                   "on_save_as_activate": self.on_save_as_activate,
                   "on_properties_activate": self.on_properties_activate,
                   "on_exit_activate": self.on_exit_activate}
                   
            wTree.signal_autoconnect (dic)

            w = wTree.get_widget("main")

            self.window=w
            self.windowTree=wTree
            self.menubar = wTree.get_widget("menubar")

            self.textbox=wTree.get_widget("outputText")
            self.more_toggle=wTree.get_widget("entryMore")
            self.entry=wTree.get_widget("entry")

            self.entry.connect('activate', self.entry_activated, None)
            self.entry.connect('key_press_event', self.key_pressed, None)

        finally:
            threads_leave()

    def on_new_activate (self, widget, data=None):
        threads_leave()
        self.change_show("unnamed", clear=1)
        threads_enter()

    def open_ok (self, widget, data=None):
        w = self.openTree.get_widget("fileSelection")
        datafile = w.get_filename()
        w.destroy()
        threads_leave()
        self.load_show(datafile)
        threads_enter()

    def open_cancel (self, widget, data=None):
        w = self.openTree.get_widget("fileSelection")
        w.destroy()
    
    def on_open_activate (self, widget, data=None):
        wTree = GladeXML ("gtklb.glade",
                          "fileSelection")
        
        dic = {"on_ok_clicked": self.open_ok,
               "on_cancel_clicked": self.open_cancel}
        
        wTree.signal_autoconnect (dic)
        
        self.openTree=wTree

    def on_save_activate (self, widget, data=None):
        if self.datafile is not None:
            self.save_show()
        else:
            self.on_save_as_activate(widget, data)

    def save_as_ok (self, widget, data=None):
        w = self.saveAsTree.get_widget("fileSelection")
        datafile = w.get_filename()
        threads_leave()
        self.save_show(datafile)
        threads_enter()
        w.destroy()

    def save_as_cancel (self, widget, data=None):
        w = self.saveAsTree.get_widget("fileSelection")
        w.destroy()
        
    def on_save_as_activate (self, widget, data=None):
        wTree = GladeXML ("gtklb.glade",
                          "fileSelection")
        
        dic = {"on_ok_clicked": self.save_as_ok,
               "on_cancel_clicked": self.save_as_cancel}
        
        wTree.signal_autoconnect (dic)
        
        self.saveAsTree=wTree

    def prop_ok (self, widget, data=None):
        w = self.propTree.get_widget("nameDialog")
        e = self.propTree.get_widget("nameEntry")
        name = e.get_text()
        threads_leave()
        self.change_show(name)
        threads_enter()
        w.destroy()

    def prop_cancel (self, widget, data=None):
        w = self.propTree.get_widget("nameDialog")
        w.destroy()

    def on_properties_activate (self, widget, data=None):
        wTree = GladeXML ("gtklb.glade",
                          "nameDialog")
        
        dic = {"on_ok_clicked": self.prop_ok,
               "on_cancel_clicked": self.prop_cancel}
        
        wTree.signal_autoconnect (dic)

        entry = wTree.get_widget("nameEntry")
        entry.set_text(self.show)
            
        self.propTree=wTree
        

    def on_exit_activate (self, widget, data=None):
        self.exit()

    def receiveData(self, data):
        print 'got data', data
        p=TreeParser()
        p.Parse(data)
        p.close()
        tree = p.tree
        for lib in self._libraries:                    
            lib.load(tree)

    def sendData(self, subtree):
        tree = DOMNode('show', {'name':self.show})
        tree.append(subtree)

        writer = TreeWriter()
        writer.write(tree)
        data = writer.get_string()
        (foo,iterator) = self.client_context.list(0)
        while 1:
            (c,b)=iterator.next_one()
            if not c:
                break
            if (b.binding_name[0].id==self.name):
                continue
            client = self.client_context.resolve(b.binding_name)
            try:
                client.receiveData(data)
            except:
                self.client_context.unbind(b.binding_name)
                


