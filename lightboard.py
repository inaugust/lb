import __main__
import sys
from threading import *
import string
import time
from gtk import *

import os
os.environ['IDLPATH']=os.environ.get('IDLPATH','')+'/usr/share/idl:/usr/local/share/idl:omniorb-core'

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

import string

class lightboard:

    _signals={}
    _event_queue=[]
    _libraries=[]

    _queue_lock=None
    _queue_count=None

    _terminated=0

    def __init__(self, datapath):
        self.datapath=datapath
        __builtins__['lb']=self

        self.orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        self.poa = self.orb.resolve_initial_references("RootPOA")
        nsi=self.orb.resolve_initial_references("NameService")
        ns = nsi._narrow(CosNaming.NamingContext)
        x=CosNaming.NameComponent("lb","Lightboard")
        x.id="lb"
        x.kind="Lightboard"
        y=[x]
        self.core = ns.resolve(y)
        print self.core
        self.poa._get_the_POAManager().activate()
        t=Thread (target=self.orb.run)
        t.start()
        self.instrument={}
        self.create_window()
        
    def run(self):
        #for x in range (1, 1025):
        #    #print x
        #    self.instrument[str(x)]=self.core.getInstrument(str(x))
        print 'a'
        print 'a'
        
    def load_libraries(self, libs):
        for lib in libs:
            print "Loading library: " + lib
            l=__import__(lib, globals(), locals(), [])
            l.initialize(self)
            self._libraries.append(l)
        print 'bye'

    def get_instrument(self, name):
        #ins = self.core.getInstrument(name)
        ins=self.instrument[name]
        return ins

    def get_fader(self, name):
        ins = self.core.getFader(name)
        return ins

    def exit (self):
        for lib in self._libraries:
            lib.shutdown()

    def level_to_percent(self, level):
        level=str(level)
        if (level[-1]=='%'):
            level=level[:-1]
        return float(level)
        
    def time_to_seconds(self, time):
        try:
            time=float(time)
            return time
        except:
            time=str(time)
        if(string.lower(time[-1])=='s'):
            return float(time[:-1])
        if(string.lower(time[-1])=='m'):
            return float(time[:-1])*60
        if(string.lower(time[-1])=='h'):
            return float(time[:-1])*60*60
        ftime=0.0
        multiple=1.0
        l=string.rfind(time, ':')
        while (l!=-1):
            n=float(time[l+1:])
            ftime=ftime+(n*multiple)
            time=time[:l]
            multiple=multiple*60.0
            if (multiple>3600):
                return None
            l=string.rfind(time, ':')
        if (len(time)):
            ftime=ftime+(float(time)*multiple)
        return ftime

    def create_window(self):
        threads_enter()
        window1=GtkWindow(WINDOW_TOPLEVEL)
        self.window=window1
        window1.set_title("Lightboard")
        window1.set_default_size(300, 200)
        window1.set_policy(FALSE, TRUE, FALSE)
        window1.set_position(WIN_POS_NONE)

        vbox1=GtkVBox()
        window1.add(vbox1)
        vbox1.set_homogeneous(FALSE)
        vbox1.set_spacing(0)

        self.menubar=GtkMenuBar()
        vbox1.pack_start(self.menubar, FALSE, FALSE, 0)

        fader_menu_item=GtkMenuItem("Fader")
        self.menubar.append(fader_menu_item)
        self.fader_menu=GtkMenu()
        fader_menu_item.set_submenu(self.fader_menu)

        window1.show_all()
        threads_leave()


        
