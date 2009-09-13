from threading import *
from xmllib import XMLParser
from ExpatXMLParser import ExpatXMLParser, DOMNode
from os import path
import lightboard
import time
import math
import gtk
from gtk import *
from gtk.glade import *
import string

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

levelfader_open_menu=None

def get_cue_keys():
    l = lb.cue.keys()
    l.sort()
    return l

def get_levelfader_keys():
    l = lb.levelfader.keys()
    l.sort()
    return l

def action_levelfader_load(args):
    lb.levelfader[args['levelfader']].setCue(args['cue'])

def action_levelfader_run(args):
    intime=args.get('time',0)
    lb.levelfader[args['levelfader']].run(args['level'], intime)

def initialize():
    reset()
    lb.program_action_type['levelfader_load'] = (
        action_levelfader_load,
        (('levelfader', get_levelfader_keys),
         ('cue', get_cue_keys)))
    lb.program_action_type['levelfader_run'] = (
        action_levelfader_run,
        (('levelfader', get_levelfader_keys), ('time', ''),
         ('level', '')))
    

def reset():
    global levelfader_open_menu
    lb.levelfader={}
    gdk.threads_enter()
    for m in lb.fader_menu.get_children():
        if (m.get_children()[0].get() == "Levelfader"):
            lb.fader_menu.remove(m)

    levelfader1=gtk.MenuItem("Levelfader")
    lb.fader_menu.append(levelfader1)
    levelfader_menu=gtk.Menu()
    levelfader1.set_submenu(levelfader_menu)

    open1=gtk.MenuItem("Open")
    levelfader_menu.append(open1)
    levelfader_open_menu=gtk.Menu()
    open1.set_submenu(levelfader_open_menu)

    new1=gtk.MenuItem("New")
    new1.connect("activate", newLevelFader_cb, None)
    levelfader_menu.append(new1)

    lb.menubar.show_all()
    gdk.threads_leave()
    
def shutdown():
    pass

def load(tree):
    for section in tree.find("levelfaders"):
        for lf in section.find("levelfader"):
            f = LevelFader (lf.attrs['name'], lf.attrs['core'])

def save():
    tree = DOMNode('levelfaders')
    for i in lb.levelfader.values():
        tree.append(i.to_tree())
    return tree

class levelFaderFactory:
    def __init__(self):
        gdk.threads_enter()
        try:
            wTree = glade.XML ("gtklb.glade",
                              "newCoreItem")
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
            e=wTree.get_widget ("nameEntry")
            coreMenu=wTree.get_widget ("coreMenu")
            
            menu=gtk.Menu()
            coreMenu.set_menu(menu)
            lb.check_cores()
            for n in lb.core_names:
                i=gtk.MenuItem(n)
                i.show()
                menu.append(i)
            coreMenu.set_history(0)
            menu.show()
            
            self.tree=wTree
        finally:
            gdk.threads_leave()
        
    def ok_clicked(self, widget, data=None):
        w = self.tree.get_widget("newCoreItem")
        e = self.tree.get_widget("nameEntry")
        name = e.get_text()
        if (string.strip(name) != ''):
            o = self.tree.get_widget("coreMenu")
            corename = o.get_children()[0].get()
            if not lb.levelfader.has_key(name):
                gdk.threads_leave()
                c = LevelFader (name, corename)
                c.send_update()
                gdk.threads_enter()
        w.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.tree.get_widget("newCoreItem")
        w.destroy()

def newLevelFader_cb(widget, data=None):
    # called from menu
    gdk.threads_leave()
    f = levelFaderFactory()
    gdk.threads_enter()
    # that's it.


class dummy:
    pass

class LevelFader (LB__POA.EventListener):
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

        gdk.threads_enter()
        try:
            fad=gtk.MenuItem(self.name)
            self.levelfader_open_menu_item=fad
            levelfader_open_menu.append(fad)
            fad.connect("activate", self.open_cb, None)
            fad.show()
        finally:
            gdk.threads_leave()


    def to_tree(self):
        xf = DOMNode('levelfader', {'name':self.name,
                                    'core':self.corename})
        return xf

    def send_update(self):
        tree = DOMNode('levelfaders')
        tree.append(self.to_tree())
        lb.sendData(tree)

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

    def clear_clicked(self, widget, data=None):
        if self.isRunning():
            self.stop()
        self.clear()
        
    def load_clicked(self, widget, data=None):
        if self.isRunning(): return
        menu = self.tree.get_widget("topCueMenu")
        name = menu.get_children()[0].get()
        self.setCue(name)
        self.setLevel(self.getLevel())
        
    def create_window (self):
        listener=self._this()
        self.level_listener_id = self.corefader.addLevelListener(listener)
        self.source_listener_id = self.corefader.addSourceListener(listener)
        self.run_listener_id = self.corefader.addRunListener(listener)
        self.stop_listener_id = self.corefader.addStopListener(listener)
        self.complete_listener_id = self.corefader.addCompleteListener(listener)
        gdk.threads_enter()
        try:
            wTree = glade.XML ("gtklb.glade",
                              "fader")
            
            dic = {"on_run_clicked": self.run_clicked,
                   "on_stop_clicked": self.stop_clicked,
                   "on_clear_clicked": self.clear_clicked,
                   "on_load_clicked": self.load_clicked}
            
            wTree.signal_autoconnect (dic)
            
            w=wTree.get_widget ("fader")
            w.connect ('destroy', self.window_destroyed)
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

            menu=gtk.Menu()
            t.set_menu(menu)
            for n in lb.cue.keys():
                i=gtk.MenuItem(n)
                i.show()
                menu.append(i)
            t.set_history(0)
            menu.show()
            
            scale = wTree.get_widget("vscale")
            self.adjustment=gtk.Adjustment(100.0, 0.0, 110.0, 1.0, 10.0, 10.0)
            self.adjustment_handler_id = self.adjustment.connect('value_changed', self.adjustment_changed, None)
            scale.set_adjustment(self.adjustment)

            self.tree=wTree
        finally:
            gdk.threads_leave()

    def levelChanged(self, evt):
        gdk.threads_enter()
        try:
            self.adjustment.disconnect(self.adjustment_handler_id)
            self.adjustment.set_value(100.0-evt.value[0])
            self.adjustment_handler_id = self.adjustment.connect('value_changed', self.adjustment_changed, None)
            self.fromSpin.set_value(evt.value[0])
            if (len(evt.value)>1):
                self.timeSpin.set_value(evt.value[1])
            gdk_flush()
        finally:
            gdk.threads_leave()

    def sourceChanged(self, evt):
        gdk.threads_enter()
        try:
            self.label.set_text("Cue: %s" % self.getCueName())
        finally:
            gdk.threads_leave()

    def runStarted(self, evt):
        gdk.threads_enter()
        try:
            w = self.tree.get_widget("run")
            w.set_sensitive(0)
            w = self.tree.get_widget("stop")
            w.set_sensitive(1)
        finally:
            gdk.threads_leave()

    def runStopped(self, evt):
        gdk.threads_enter()
        try:
            w = self.tree.get_widget("run")
            w.set_sensitive(1)
            w = self.tree.get_widget("stop")
            w.set_sensitive(0)
        finally:
            gdk.threads_leave()

    def runCompleted(self, evt):
        gdk.threads_enter()
        try:
            w = self.tree.get_widget("run")
            w.set_sensitive(1)
            w = self.tree.get_widget("stop")
            w.set_sensitive(0)
        finally:
            gdk.threads_leave()
        
    def receiveEvent(self, evt):
        try:
            m = self.event_mapping[evt.type]
            m(evt)
        except:
            pass

    def window_destroyed (self, widget, data=None):
        self.corefader.removeLevelListener(self.level_listener_id)
        self.corefader.removeSourceListener(self.source_listener_id)
        self.corefader.removeRunListener(self.run_listener_id)
        self.corefader.removeStopListener(self.stop_listener_id)
        self.corefader.removeCompleteListener(self.complete_listener_id)

        self.levelfader_open_menu_item.set_sensitive(1)        

    def open_cb(self, widget, data):
        """ Called from lightboard->fader->levelfader"""

        self.levelfader_open_menu_item.set_sensitive(0)
        gdk.threads_leave()
        self.create_window()
        gdk.threads_enter()

# see gtk_signal_handler_block_by_func
# at http://developer.gnome.org/doc/API/gtk/gtkeditable.html
