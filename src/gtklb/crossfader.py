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


class crossfader(LB__POA.EventListener):
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

        threads_enter()
        try:
            fad=GtkMenuItem(self.name)
            self.crossfader_open_menu_item=fad
            crossfader_open_menu.append(fad)
            fad.connect("activate", self.open_cb, None)
            fad.show()
        finally:
            threads_leave()


    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s=s+sp+'<crossfader name="%s" core="%s"/>\n' % (self.name,
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
        return self.corefader.getLevel()

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
            #print 'updating fader'
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

        if (self.getLevel()!=start):
            self.setLevel(start)

        print 'setting times', downtime, uptime
        self.setTimes(downtime, uptime)
        if (downtime>uptime): intime=downtime
        else: intime=uptime

        self.run(end, intime)

    def stop_clicked(self, widget, data=None):
        if not self.isRunning(): return
        self.stop()

    def load_clicked(self, widget, data=None):
        if self.isRunning(): return
        menu = self.tree.get_widget("topCueMenu")
        upname = menu.children()[0].get()
        menu = self.tree.get_widget("bottomCueMenu")
        downname = menu.children()[0].get()
        self.setCues(downname, upname)
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
            w.set_title("Crossfader %s" % self.name)

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

            menu=GtkMenu()
            t.set_menu(menu)
            for n in lb.cue.keys():
                i=GtkMenuItem(n)
                i.show()
                menu.append(i)
            t.set_history(0)
            menu.show()

            menu=GtkMenu()
            b.set_menu(menu)
            for n in lb.cue.keys():
                i=GtkMenuItem(n)
                i.show()
                menu.append(i)
            b.set_history(0)
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
            threads_leave()

    def sourceChanged(self, evt):
        threads_enter()
        try:
            self.up_label.set_text("Up Cue: %s" % self.getUpCueName())
            self.down_label.set_text("Down Cue: %s" % self.getDownCueName())
        finally:
            threads_leave()

    def runStarted(self, evt):
        self.core_intime = evt.value[1]
        self.core_uptime = self.corefader.getUpCueTime()
        self.core_downtime = self.corefader.getDownCueTime()
        print 'start:', self.core_intime, self.core_downtime, self.core_uptime
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
#         try:
#             m = self.event_mapping[evt.type]
#             m(evt)
#         except:
#             print evt.type
#             print 'exception'
          m = self.event_mapping[evt.type]
          m(evt)

    def open_cb(self, widget, data):
        """ Called from lightboard->fader->crossfader"""

        self.crossfader_open_menu_item.set_sensitive(0)
        threads_leave()
        self.create_window()
        threads_enter()

# see gtk_signal_handler_block_by_func
# at http://developer.gnome.org/doc/API/gtk/gtkeditable.html
