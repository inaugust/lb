from threading import *
from xmllib import XMLParser
from ExpatXMLParser import ExpatXMLParser
from os import path
from gtk import *
from libglade import *

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

crossfader_open_menu=None

def initialize():
    reset()

def reset():
    global crossfader_open_menu
    lb.crossfader={}

    threads_enter()
    for m in lb.fader_menu.children():
        if (m.children()[0].get() == "Crossfader"):
            lb.fader_menu.remove(m)

    crossfader1=GtkMenuItem("Crossfader")
    lb.fader_menu.append(crossfader1)
    crossfader_menu=GtkMenu()
    crossfader1.set_submenu(crossfader_menu)

    open1=GtkMenuItem("Open")
    crossfader_menu.append(open1)
    crossfader_open_menu=GtkMenu()
    open1.set_submenu(crossfader_open_menu)

    new1=GtkMenuItem("New")
    new1.connect("activate", newCrossFader_cb, None)
    crossfader_menu.append(new1)

    lb.menubar.show_all()
    threads_leave()

def shutdown():
    pass

def load(data):
    p=parser()
    p.Parse(data)
    p.close()

def save():
    s="<crossfaders>\n\n"
    for c in lb.crossfader.values():
        s=s+c.to_xml(1)
    s=s+"</crossfaders>\n"
    return s

class crossFaderFactory:
    def __init__(self):
        print 'props'
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "newCoreItem")
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
            e=wTree.get_widget ("nameEntry")
            coreMenu=wTree.get_widget ("coreMenu")
            
            menu=GtkMenu()
            coreMenu.set_menu(menu)
            lb.check_cores()
            for n in lb.core_names:
                i=GtkMenuItem(n)
                i.show()
                menu.append(i)
            coreMenu.set_history(0)
            menu.show()
            
            self.tree=wTree
        finally:
            threads_leave()
        
    def ok_clicked(self, widget, data=None):
        w = self.tree.get_widget("newCoreItem")
        e = self.tree.get_widget("nameEntry")
        name = e.get_text()
        o = self.tree.get_widget("coreMenu")
        corename = o.children()[0].get()
        if not lb.crossfader.has_key(name):
            threads_leave()
            c = crossfader(name, corename)
            threads_enter()
        w.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.tree.get_widget("newCoreItem")
        w.destroy()

def newCrossFader_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = crossFaderFactory()
    threads_enter()
    # that's it.

class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_crossfaders=0

    def start_crossfaders (self, attrs):
        self.in_crossfaders=1

    def end_crossfaders (self):
        self.in_crossfaders=0
        
    def start_crossfader (self, attrs):
        if (not self.in_crossfaders): return
        self.crossfader=crossfader (attrs['name'], attrs['core'])

    def end_crossfader (self):
        if (not self.in_crossfaders): return
        

class crossfader(LB__POA.FaderLevelListener):
    """ Python wrapper for core Crossfader class"""

    def __init__(self, name, corename):
        self.name=name
        self.corename=corename
        self.corefader=lb.get_fader(name)
        if (self.corefader is not None):
            e=0
            try:
                e=self.corefader._non_existent()
            except:
                self.corefader=None
            if (e): self.corefader=None
        if (self.corefader is None):
            c = lb.get_core(corename)
            c.createCrossFader (lb.show, name)
        self.corefader=lb.get_fader(name)

        listener=self._this()
        print listener
        print self.corefader
        self.corefader.addLevelListener(listener)

        if (lb.crossfader.has_key(self.name)):
            oldxf = lb.crossfader[self.name]
            crossfader_open_menu.remove(oldxf.crossfader_open_menu_item)
        lb.crossfader[self.name]=self

        threads_enter()
        try:
            fad=GtkMenuItem(self.name)
            self.crossfader_open_menu_item=fad
            crossfader_open_menu.append(fad)
            fad.connect("activate", self.open_cb, None)
            fad.show()
        finally:
            threads_leave()

        #FIXME

    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s=s+sp+'<crossfader name="%s" core="%s"/>\n' % (self.name,
                                                        self.corename)
        return s

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
        try:
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
            window.show_all()
        finally:
            threads_leave()

    def levelChanged(self, evt):
        threads_enter()
        try:
            self.adjustment.disconnect(self.adjustment_handler_id)
            self.adjustment.set_value(100.0-evt.value[0])
            self.adjustment_handler_id = self.adjustment.connect('value_changed', self.adjustment_changed, None)
            gdk_flush()
        finally:
            threads_leave()

    def open_cb(self, widget, data):
        """ Called from lightboard->fader->crossfader"""

        self.crossfader_open_menu_item.set_sensitive(0)
        threads_leave()
        self.create_window()
        threads_enter()

# see gtk_signal_handler_block_by_func
# at http://developer.gnome.org/doc/API/gtk/gtkeditable.html
