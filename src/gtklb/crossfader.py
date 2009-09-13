from threading import *
from xmllib import XMLParser
from ExpatXMLParser import ExpatXMLParser, DOMNode
from os import path
import gtk
from gtk import *
from gtk.glade import *
import string
from cue import Cue

from omniORB import CORBA
import CosNaming
from idl import LB, LB__POA

crossfader_open_menu=None


def action_crossfader_load(args):
    xf = lb.crossfader[args['crossfader']]
    if xf.isRunning():
        xf.stop()
    old_cue = xf.getUpCueName()
    if (old_cue and lb.cue.has_key(old_cue)):
        cue1=lb.cue[old_cue]
    else:
        old_cue = xf.getDownCueName()
        if (old_cue and lb.cue.has_key(old_cue)):
            cue1=lb.cue[old_cue]
        else:
            cue1=Cue("")
    cue2=lb.cue[args['cue']]
    xf.setCues (cue1, cue2)
    xf.setLevel(0.0)

def action_crossfader_run(args):
    xf = lb.crossfader[args['crossfader']]
  
    uptime=lb.value_to_core('time', args.get('uptime', 0))
    downtime=lb.value_to_core('time', args.get('downtime', 0))
    xf.setTimes(uptime, downtime)

    if (downtime>uptime): intime=downtime
    else: intime=uptime
    intime=args.get('time', intime)
    xf.run(100.0, intime)

def get_cue_keys():
    l = lb.cue.keys()
    l.sort()
    return l

def get_crossfader_keys():
    l = lb.crossfader.keys()
    l.sort()
    return l

def initialize():
    reset()
    lb.program_action_type['crossfader_load'] = (
        action_crossfader_load,
        (('crossfader', get_crossfader_keys),
         ('cue', get_cue_keys)))
    lb.program_action_type['crossfader_run'] = (
        action_crossfader_run,
        (('crossfader', get_crossfader_keys),
         ('uptime', ''),
         ('downtime', '')))


def reset():
    global crossfader_open_menu
    lb.crossfader={}

    gdk.threads_enter()
    for m in lb.fader_menu.get_children():
        if (m.get_children()[0].get() == "Crossfader"):
            lb.fader_menu.remove(m)

    crossfader1=gtk.MenuItem("Crossfader")
    lb.fader_menu.append(crossfader1)
    crossfader_menu=gtk.Menu()
    crossfader1.set_submenu(crossfader_menu)

    open1=gtk.MenuItem("Open")
    crossfader_menu.append(open1)
    crossfader_open_menu=gtk.Menu()
    open1.set_submenu(crossfader_open_menu)

    new1=gtk.MenuItem("New")
    new1.connect("activate", newCrossFader_cb, None)
    crossfader_menu.append(new1)

    lb.menubar.show_all()
    gdk.threads_leave()

def shutdown():
    pass

def load(tree):
    for section in tree.find("crossfaders"):
        for xf in section.find("crossfader"):
            c = CrossFader (xf.attrs['name'], xf.attrs['core'])

def save():
    tree = DOMNode('crossfaders')
    for i in lb.crossfader.values():
        tree.append(i.to_tree())
    return tree

class crossFaderFactory:
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
            if not lb.crossfader.has_key(name):
                gdk.threads_leave()
                c = CrossFader(name, corename)
                c.send_update()
                gdk.threads_enter()
        w.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.tree.get_widget("newCoreItem")
        w.destroy()

def newCrossFader_cb(widget, data=None):
    # called from menu
    gdk.threads_leave()
    f = crossFaderFactory()
    gdk.threads_enter()
    # that's it.


class CrossFader(LB__POA.EventListener):
    """ Python wrapper for core Crossfader class"""

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
            c.createCrossFader (lb.show, name)
        self.corefader=lb.get_fader(name)

        if (lb.crossfader.has_key(self.name)):
            oldxf = lb.crossfader[self.name]
            crossfader_open_menu.remove(oldxf.crossfader_open_menu_item)

        lb.crossfader[self.name]=self

        gdk.threads_enter()
        try:
            fad=gtk.MenuItem(self.name)
            self.crossfader_open_menu_item=fad
            crossfader_open_menu.append(fad)
            fad.connect("activate", self.open_cb, None)
            fad.show()
        finally:
            gdk.threads_leave()


    def to_tree(self):
        xf = DOMNode('crossfader', {'name':self.name,
                                    'core':self.corename})
        return xf

    def send_update(self):
        tree = DOMNode('crossfaders')
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

    def setCues(self, downcue, upcue):
        if (type(upcue) == type('')):
            upcue=lb.cue[upcue]
        if (type(downcue) == type('')):
            downcue=lb.cue[downcue]
        return self.corefader.setCues(downcue.core_cue, upcue.core_cue)

    def setTimes(self, downtime, uptime):
        uptime=lb.value_to_core('time', uptime)
        downtime=lb.value_to_core('time', downtime)
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
            uptime = self.tree.get_widget("topTimeSpin")
            downtime = self.tree.get_widget("bottomTimeSpin")

            uptime = uptime.get_value_as_float()
            downtime = downtime.get_value_as_float()

            self.setTimes(downtime, uptime)

            self.corefader.setLevel(100.0-widget.value)

    def run_clicked(self, widget, data=None):
        if self.isRunning(): return
        start = self.tree.get_widget("fromSpin")
        end = self.tree.get_widget("toSpin")
        uptime = self.tree.get_widget("topTimeSpin")
        downtime = self.tree.get_widget("bottomTimeSpin")

        start = start.get_value_as_float()
        end = end.get_value_as_float()
        uptime = uptime.get_value_as_float()
        downtime = downtime.get_value_as_float()

        if (lb.value_to_core('level', self.getLevel())[0]!=start):
            self.setLevel(start)

        self.setTimes(downtime, uptime)
        if (downtime>uptime): intime=downtime
        else: intime=uptime

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
        upname = menu.get_children()[0].get()
        menu = self.tree.get_widget("bottomCueMenu")
        downname = menu.get_children()[0].get()
        self.setCues(downname, upname)
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
            w.set_title("Crossfader %s" % self.name)
            w.connect ('destroy', self.window_destroyed)

            t=wTree.get_widget ("topLabel")
            b=wTree.get_widget ("bottomLabel")
            t.set_text("Up Cue: ---")
            b.set_text("Down Cue: ---")
            self.up_label=t
            self.down_label=b

            t=wTree.get_widget ("topCueLabel")
            b=wTree.get_widget ("bottomCueLabel")
            t.set_text("Up Cue")
            b.set_text("Down Cue")

            t=wTree.get_widget ("topTimeLabel")
            b=wTree.get_widget ("bottomTimeLabel")
            t.set_text("Up Time")
            b.set_text("Down Time")

            self.fromSpin=wTree.get_widget ("fromSpin")
            self.toSpin=wTree.get_widget ("toSpin")
            self.upTimeSpin=wTree.get_widget ("topTimeSpin")
            self.downTimeSpin=wTree.get_widget ("bottomTimeSpin")

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

            menu=gtk.Menu()
            t.set_menu(menu)
            for n in lb.cue.keys():
                i=gtk.MenuItem(n)
                i.show()
                menu.append(i)
            t.set_history(0)
            menu.show()

            menu=gtk.Menu()
            b.set_menu(menu)
            for n in lb.cue.keys():
                i=gtk.MenuItem(n)
                i.show()
                menu.append(i)
            b.set_history(0)
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
                utr = self.core_intime / self.core_uptime
                dtr = self.core_intime / self.core_downtime
                ratio = (self.core_intime-evt.value[1]) / self.core_intime
                if (utr<1.0 or dtr<1.0):
                    if(utr<dtr):
                        r=1.0/utr
                        dtr=r*dtr
                    else:
                        r=1.0/dtr
                        utr=r*utr
                utr = self.core_uptime-(self.core_uptime * ratio * utr)
                dtr = self.core_downtime-(self.core_downtime * ratio * dtr)
                self.upTimeSpin.set_value(utr)
                self.downTimeSpin.set_value(dtr)
            gdk_flush()
        finally:
            gdk.threads_leave()

    def sourceChanged(self, evt):
        gdk.threads_enter()
        try:
            self.up_label.set_text("Up Cue: %s" % self.getUpCueName())
            self.down_label.set_text("Down Cue: %s" % self.getDownCueName())
        finally:
            gdk.threads_leave()

    def runStarted(self, evt):
        self.core_intime = evt.value[1]
        self.core_uptime = self.corefader.getUpCueTime()
        self.core_downtime = self.corefader.getDownCueTime()
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

    def window_destroyed(self, widget, data=None):
        self.corefader.removeLevelListener(self.level_listener_id)
        self.corefader.removeSourceListener(self.source_listener_id)
        self.corefader.removeRunListener(self.run_listener_id)
        self.corefader.removeStopListener(self.stop_listener_id)
        self.corefader.removeCompleteListener(self.complete_listener_id)
        self.crossfader_open_menu_item.set_sensitive(1)        

    def open_cb(self, widget, data):
        """ Called from lightboard->fader->crossfader"""

        self.crossfader_open_menu_item.set_sensitive(0)
        gdk.threads_leave()
        self.create_window()
        gdk.threads_enter()

# see gtk_signal_handler_block_by_func
# at http://developer.gnome.org/doc/API/gtk/gtkeditable.html
