from threading import *
from xmllib import XMLParser
from ExpatXMLParser import ExpatXMLParser
from os import path
import lightboard
import time
import math
from gtk import *
from libglade import *
import string

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

levelfader_open_menu=None

def initialize():
    reset()

def reset():
    global levelfader_open_menu
    lb.levelfader={}
    threads_enter()
    for m in lb.fader_menu.children():
        if (m.children()[0].get() == "Levelfader"):
            lb.fader_menu.remove(m)

    levelfader1=GtkMenuItem("Levelfader")
    lb.fader_menu.append(levelfader1)
    levelfader_menu=GtkMenu()
    levelfader1.set_submenu(levelfader_menu)

    open1=GtkMenuItem("Open")
    levelfader_menu.append(open1)
    levelfader_open_menu=GtkMenu()
    open1.set_submenu(levelfader_open_menu)

    new1=GtkMenuItem("New")
    new1.connect("activate", newLevelFader_cb, None)
    levelfader_menu.append(new1)

    lb.menubar.show_all()
    threads_leave()
    
def shutdown():
    pass

def load(data):
    p=parser()
    p.Parse(data)
    p.close()

def save():
    s="<levelfaders>\n\n"
    for c in lb.levelfader.values():
        s=s+c.to_xml(1)
    s=s+"</levelfaders>\n"
    return s

class levelFaderFactory:
    def __init__(self):
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
        if (string.strip(name) != ''):
            o = self.tree.get_widget("coreMenu")
            corename = o.children()[0].get()
            if not lb.levelfader.has_key(name):
                threads_leave()
                c = levelfader(name, corename)
                threads_enter()
        w.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.tree.get_widget("newCoreItem")
        w.destroy()

def newLevelFader_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = levelFaderFactory()
    threads_enter()
    # that's it.


class dummy:
    pass

class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_levelfaders=0

    def start_levelfaders (self, attrs):
        self.in_levelfaders=1

    def end_levelfaders (self):
        self.in_levelfaders=0

    def start_levelfader (self, attrs):
        if (not self.in_levelfaders): return
        name=attrs['name']
        core=attrs['core']
        self.levelfader = levelfader (name, core)

class levelfader(LB__POA.EventListener):
    """ Python wrapper for core Levelfader class"""
    
    def __init__(self, name, corename):
        self.event_mapping = {LB.event_fader_level: self.levelChanged,
                              LB.event_fader_source: self.sourceChanged,
                              LB.event_fader_run: self.runStarted,
                              LB.event_fader_stop: self.runStopped,
                              LB.event_fader_complete: self.runCompleted}
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
            c.createLevelFader (lb.show, name)
        self.corefader=lb.get_fader(name)

        if (lb.levelfader.has_key(self.name)):
            oldf = lb.levelfader[self.name]
            levelfader_open_menu.remove(oldf.levelfader_open_menu_item)
        lb.levelfader[self.name]=self

        threads_enter()
        try:
            fad=GtkMenuItem(self.name)
            self.levelfader_open_menu_item=fad
            levelfader_open_menu.append(fad)
            fad.connect("activate", self.open_cb, None)
            fad.show()
        finally:
            threads_leave()


    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s=s+sp+'<levelfader name="%s" core="%s"/>\n' % (self.name,
                                                        self.corename)
        return s

    def run(self, level, time):
        time=lb.value_to_core('time', time)
        level=lb.value_to_core('level', level)[0]
        return self.corefader.run(level, time)

    def stop(self):
        return self.corefader.stop()

    def setLevel(self, level):
        return self.corefader.setLevel(lb.value_to_core('level', level)[0])

    def getLevel(self):
        return lb.value_to_string('level', [self.corefader.getLevel()])

    def isRunning(self):
        return self.corefader.isRunning()

    def setCue(self, cue):
        if (type(cue) == type('')):
            return self.corefader.setCue(lb.cue[cue].core_cue)
        else:
            return self.corefader.setCue(cue.core_cue)

    def setTime(self, time):
        time=lb.value_to_core('time', time)
        return self.corefader.setTime(time)

    def getCueName(self):
        return self.corefader.getCueName()
    
    def clear(self):
        return self.corefader.clear()

    #private

    def adjustment_changed(self, widget, data):
        if (not self.corefader.isRunning()):
            self.corefader.setLevel(100.0-widget.value)

    def run_clicked(self, widget, data=None):
        if self.isRunning(): return
        start = self.tree.get_widget("fromSpin")
        end = self.tree.get_widget("toSpin")
        intime = self.tree.get_widget("topTimeSpin")

        start = start.get_value_as_float()
        end = end.get_value_as_float()
        intime = intime.get_value_as_float()

        if (self.getLevel()!=start):
            self.setLevel(start)
        
        self.run(end, intime)

    def stop_clicked(self, widget, data=None):
        if not self.isRunning(): return
        self.stop()

    def load_clicked(self, widget, data=None):
        if self.isRunning(): return
        menu = self.tree.get_widget("topCueMenu")
        name = menu.children()[0].get()
        self.setCue(name)
        self.setLevel(self.getLevel())
        
    def create_window (self):
        listener=self._this()
        self.corefader.addLevelListener(listener)
        self.corefader.addSourceListener(listener)
        self.corefader.addRunListener(listener)
        self.corefader.addStopListener(listener)
        self.corefader.addCompleteListener(listener)
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "fader")
            
            dic = {"on_run_clicked": self.run_clicked,
                   "on_stop_clicked": self.stop_clicked,
                   "on_load_clicked": self.load_clicked}
            
            wTree.signal_autoconnect (dic)
            
            w=wTree.get_widget ("fader")
            w.set_title("Levelfader %s" % self.name)

            t=wTree.get_widget ("topLabel")
            b=wTree.get_widget ("bottomLabel")
            t.set_text("Cue: ---")
            b.set_text("")
            self.label=t

            t=wTree.get_widget ("topCueLabel")
            b=wTree.get_widget ("bottomCueLabel")
            t.set_text("Cue")
            b.set_text("")

            t=wTree.get_widget ("topTimeLabel")
            b=wTree.get_widget ("bottomTimeLabel")
            t.set_text("Time")
            b.set_text("")

            b=wTree.get_widget ("bottomTimeSpin")
            b.hide()

            self.fromSpin=wTree.get_widget ("fromSpin")
            self.toSpin=wTree.get_widget ("toSpin")
            self.timeSpin=wTree.get_widget ("topTimeSpin")

            r = wTree.get_widget("run")
            s = wTree.get_widget("stop")
            if (self.isRunning()):
                r.set_sensitive(0)
                s.set_sensitive(1)
            else:
                r.set_sensitive(1)
                s.set_sensitive(0)

            t=wTree.get_widget ("topCueMenu")
            b=wTree.get_widget ("bottomCueMenu")
            b.hide()

            menu=GtkMenu()
            t.set_menu(menu)
            for n in lb.cue.keys():
                i=GtkMenuItem(n)
                i.show()
                menu.append(i)
            t.set_history(0)
            menu.show()
            
            scale = wTree.get_widget("vscale")
            self.adjustment=GtkAdjustment(100.0, 0.0, 110.0, 1.0, 10.0, 10.0)
            self.adjustment_handler_id = self.adjustment.connect('value_changed', self.adjustment_changed, None)
            scale.set_adjustment(self.adjustment)

            self.tree=wTree
        finally:
            threads_leave()

    def levelChanged(self, evt):
        threads_enter()
        try:
            self.adjustment.disconnect(self.adjustment_handler_id)
            self.adjustment.set_value(100.0-evt.value[0])
            self.adjustment_handler_id = self.adjustment.connect('value_changed', self.adjustment_changed, None)
            self.fromSpin.set_value(evt.value[0])
            if (len(evt.value)>1):
                self.timeSpin.set_value(evt.value[1])
            gdk_flush()
        finally:
            threads_leave()

    def sourceChanged(self, evt):
        threads_enter()
        try:
            self.label.set_text("Cue: %s" % self.getCueName())
        finally:
            threads_leave()

    def runStarted(self, evt):
        threads_enter()
        try:
            w = self.tree.get_widget("run")
            w.set_sensitive(0)
            w = self.tree.get_widget("stop")
            w.set_sensitive(1)
        finally:
            threads_leave()

    def runStopped(self, evt):
        threads_enter()
        try:
            w = self.tree.get_widget("run")
            w.set_sensitive(1)
            w = self.tree.get_widget("stop")
            w.set_sensitive(0)
        finally:
            threads_leave()

    def runCompleted(self, evt):
        threads_enter()
        try:
            w = self.tree.get_widget("run")
            w.set_sensitive(1)
            w = self.tree.get_widget("stop")
            w.set_sensitive(0)
        finally:
            threads_leave()
        
    def receiveEvent(self, evt):
        try:
            m = self.event_mapping[evt.type]
            m(evt)
        except:
            pass

    def open_cb(self, widget, data):
        """ Called from lightboard->fader->levelfader"""

        self.levelfader_open_menu_item.set_sensitive(0)
        threads_leave()
        self.create_window()
        threads_enter()

# see gtk_signal_handler_block_by_func
# at http://developer.gnome.org/doc/API/gtk/gtkeditable.html
