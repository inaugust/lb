import __main__
import sys
from threading import *
import string
import time
from gtk import *
import GDK
from rexec import RExec
import __builtin__
import __main__
from completion import completion
import instrument

import os
os.environ['IDLPATH']=os.environ.get('IDLPATH','')+'/usr/share/idl:/usr/local/share/idl:omniorb-core'

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

import string

COPYRIGHT="Copyright 2001 In August Productions, INC."

class lightboard(completion):

    _signals={}
    _event_queue=[]
    _libraries=[]

    _queue_lock=None
    _queue_count=None

    _terminated=0

    def __init__(self, show, datapath):
        completion.__init__(self, {'lb':self})
        self.datapath=datapath
        self.show=show
        __builtins__['lb']=self

        self.orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        self.poa = self.orb.resolve_initial_references("RootPOA")
        nsi=self.orb.resolve_initial_references("NameService")
        ns = nsi._narrow(CosNaming.NamingContext)
        self.root_naming = ns

        try:
            x=CosNaming.NameComponent("shows","")
            o = self.root_naming.resolve([x])
        except:
            o = self.root_naming.bind_new_context([x])

        try:
            x=CosNaming.NameComponent(self.show,"")
            o = o.resolve([x])
        except:
            o = o.bind_new_context([x])

        try:
            x=CosNaming.NameComponent("instruments","")
            ins_ctx = o.resolve([x])
        except:
            ins_ctx = o.bind_new_context([x])

        try:
            x=CosNaming.NameComponent("faders","")
            fad_ctx = o.resolve([x])
        except:
            fad_ctx = o.bind_new_context([x])

        self.instrument_context = ins_ctx
        self.fader_context = fad_ctx

        self.poa._get_the_POAManager().activate()
        t=Thread (target=self.orb.run)
        t.start()

        self.create_window()

        
    def run(self):
        #for x in range (1, 1025):
        #    #print x
        #    self.instrument[str(x)]=self.core.getInstrument(str(x))
        self.write ("GTK Lightboard client\n")
        self.write (COPYRIGHT+"\n")
        self.write ("Working in show: %s\n" % self.show)

        names=''
        x=CosNaming.NameComponent("lightboards","")
        o = self.root_naming.resolve([x])
        (foo,iterator) = o.list(0)
        while 1:
            (c,b)=iterator.next_one()
            if not c:
                break
            names=names + " " + str(b.binding_name[0].id)
        
        self.write ("Connected to core dimmer controlers: %s \n" % names)
        self.write ("Ready.\n")
        
    def load_libraries(self, libs):
        for lib in libs:
            print "Loading library: " + lib
            l=__import__(lib, globals(), locals(), [])
            l.initialize(self)
            self._libraries.append(l)

    def exit (self):
        for lib in self._libraries:
            lib.shutdown()

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
        #deprecated
        print "DON'T USE GET_CORE!"
        x=CosNaming.NameComponent("lightboards", "")
        o = self.root_naming.resolve([x])
        x=CosNaming.NameComponent(name, "")
        o = o.resolve([x])
        x=CosNaming.NameComponent("lb", "Lightboard")
        o = o.resolve([x])
        return o

    def core_attr_id (self, name):
        return instrument.attribute_mapping[name][0]

    def attr_widget (self, name):
        return instrument.attribute_mapping[name][1]
            
    def value_to_string(self, name, value):
        return instrument.attribute_mapping[name][3](value)

    def value_to_core(self, name, value):
        return instrument.attribute_mapping[name][2](value)

    def create_window(self):
        threads_enter()
        window1=GtkWindow(WINDOW_TOPLEVEL)
        self.window=window1
        window1.set_title("Lightboard")
        window1.set_usize(-1, -1)
        window1.set_default_size(300, 200)
        window1.set_policy(FALSE, TRUE, FALSE)
        window1.set_position(WIN_POS_NONE)

        vbox1=GtkVBox()
        window1.add(vbox1)
        vbox1.set_homogeneous(FALSE)
        vbox1.set_usize(-1, -1)
        vbox1.set_spacing(0)

        self.menubar=GtkMenuBar()
        self.menubar.set_usize(-1, -1)
        vbox1.pack_start(self.menubar, FALSE, FALSE, 0)

        fader_menu_item=GtkMenuItem("Fader")
        self.menubar.append(fader_menu_item)
        self.fader_menu=GtkMenu()
        fader_menu_item.set_submenu(self.fader_menu)

        scrolledwindow1=GtkScrolledWindow()
        vbox1.pack_start(scrolledwindow1, TRUE, TRUE, 0)
        scrolledwindow1.set_usize(-1, -1)
        scrolledwindow1.set_policy(POLICY_AUTOMATIC, POLICY_AUTOMATIC)
        text1=GtkText()
        text1.set_usize(-1, -1)
        scrolledwindow1.add(text1)
        #text1.set_flags(CAN_FOCUS)
        text1.set_editable(FALSE)
        text1.show()
        self.textbox=text1

        hbox1=GtkHBox()
        vbox1.pack_start(hbox1, FALSE, FALSE, 0)
        hbox1.set_usize(-1, -1)
        hbox1.set_homogeneous(FALSE)
        hbox1.set_spacing(0)
        togglebutton1=GtkToggleButton("More...")
        hbox1.pack_start(togglebutton1, FALSE, FALSE, 0)
        togglebutton1.set_flags(CAN_FOCUS)
        togglebutton1.set_usize(-1, -1)
        togglebutton1.set_sensitive(0)
        togglebutton1.show()
        self.more_toggle=togglebutton1

        entry1=GtkEntry()
        entry1.set_usize(-1, -1)
        hbox1.pack_start(entry1, TRUE, TRUE, 0)
        entry1.set_flags(CAN_FOCUS)
        entry1.set_editable(TRUE)
        entry1.show()
        self.entry=entry1

        entry1.connect('activate', self.entry_activated, None)
        entry1.connect('key_press_event', self.key_pressed, None)
        window1.show_all()
        threads_leave()


        
