from threading import *
from xmllib import XMLParser
from ExpatXMLParser import ExpatXMLParser
from os import path
from gtk import *

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

crossfader_menu=None

def initialize(lb):
    global crossfader_menu
    lb.crossfader={}

    threads_enter()
    crossfader1=GtkMenuItem("Crossfader")
    lb.fader_menu.append(crossfader1)
    crossfader_menu=GtkMenu()
    crossfader1.set_submenu(crossfader_menu)

    lb.menubar.show_all()
    threads_leave()

    try:
        f=open(path.join(lb.datapath, 'crossfaders'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()
    
def shutdown():
    pass

class parser(ExpatXMLParser):

    def start_crossfader (self, attrs):
        self.crossfader=crossfader (attrs['name'])

    def end_crossfader (self):
        lb.crossfader[self.crossfader.name]=self.crossfader

        threads_enter()
        fad=GtkMenuItem(self.crossfader.name)
        self.crossfader.crossfader_menu_item=fad
        crossfader_menu.append(fad)
        fad.connect("activate", self.crossfader.open_cb, None)
        fad.show()
        threads_leave()
        self.crossfader.create_window()


class crossfader(LB__POA.FaderLevelListener):
    """ Python wrapper for core Crossfader class"""

    def __init__(self, name):
        self.name=name
        self.corefader=lb.get_fader('X1')

        listener=self._this()
        print listener
        self.corefader.addLevelListener(listener)

        #FIXME

    def run(self, level, time):
        time=lb.time_to_seconds(time)
        level=lb.level_to_percent(level)
        return self.corefader.run(level, time)

    def stop(self):
        return self.corefader.stop()

    def setLevel(self, level):
        return self.corefader.setLevel(float(level))

    def isRunning(self):
        return self.corefader.isRunning()

    def setCues(self, downcue, upcue):
        return self.corefader.setCues(downcue.core_cue, upcue.core_cue)

    def setTimes(self, downtime, uptime):
        downtime=lb.time_to_seconds(downtime)
        uptime=lb.time_to_seconds(uptime)
        return self.corefader.setTimes(downtime, uptime)

    def getUpCueName(self):
        return self.corefader.getUpCueName()
    
    def getDownCueName(self):
        return self.corefader.getDownCueName()

    def clear(self):
        return self.corefader.clear()

    # UI methods

    def adjustment_changed(self, widget, data):
        if (not self.corefader.isRunning()):
            #print 'updating fader'
            self.corefader.setLevel(100.0-widget.value)

    def create_window (self):
        threads_enter()
        window=GtkWindow(WINDOW_TOPLEVEL)
        self.window=window
        window.set_title("Crossfader")
        window.set_default_size(150, 300)
        window.set_policy(FALSE, TRUE, FALSE)
        window.set_position(WIN_POS_NONE)
        
        vbox=GtkVBox()
        window.add(vbox)
        vbox.set_homogeneous(FALSE)
        vbox.set_spacing(0)

        self.label_up=GtkLabel("Up: ---")
        self.label_down=GtkLabel("Dn: ---")
        
        vbox.pack_start(self.label_up, FALSE, FALSE, 0)
        vbox.pack_start(self.label_down, FALSE, FALSE, 0)

        self.adjustment=GtkAdjustment(100.0, 0.0, 110.0, 1.0, 10.0, 10.0)
        self.adjustment_handler_id = self.adjustment.connect('value_changed', self.adjustment_changed, None)
        scale = GtkVScale (self.adjustment)
        scale.set_draw_value(0);
        #scrollbar=GtkVScrollbar(self.adjustment)
        scale.set_usize(0, 200)

        vbox.pack_start(scale, FALSE, FALSE, 0)

        threads_leave()

    def levelChanged(self, evt):
        threads_enter()
        self.adjustment.disconnect(self.adjustment_handler_id)
        self.adjustment.set_value(100.0-evt.value[0])
        self.adjustment_handler_id = self.adjustment.connect('value_changed', self.adjustment_changed, None)
        gdk_flush()
        threads_leave()

    def open_cb(self, widget, data):
        """ Called from lightboard->fader->crossfader"""

        self.crossfader_menu_item.set_sensitive(0)
        self.window.show_all()
