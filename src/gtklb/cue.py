from xmllib import XMLParser
from os import path
import string
import lightboard
from ExpatXMLParser import ExpatXMLParser
from gtk import *
from libglade import *
from completion import completion
import time
import instrument
import string
import cue_edit

from omniORB import CORBA
from idl import LB, LB__POA

edit_menu=None

def initialize():
    reset()

def reset():
    global edit_menu
    lb.cue={}
    threads_enter()
    menubar=lb.menubar
    for m in menubar.children():
        if (m.children()[0].get() == "Cue"):
            menubar.remove(m)

    cue1=GtkMenuItem("Cue")
    menubar.append(cue1)

    cue1_menu=GtkMenu()
    cue1.set_submenu(cue1_menu)

    edit1=GtkMenuItem("Edit")
    cue1_menu.append(edit1)
    edit_menu=GtkMenu()
    edit1.set_submenu(edit_menu)

    new1=GtkMenuItem("New")
    new1.connect("activate", newCue_cb, None)
    cue1_menu.append(new1)

    menubar.show_all()
    threads_leave()
        
def shutdown():
    pass

def load(data):
    p=parser()
    p.Parse(data)
    p.close()

def save():
    s="<cues>\n\n"
    for c in lb.cue.values():
        s=s+c.to_xml(1)+"\n"
    s=s+"</cues>\n"
    return s

def newCue_cb(widget, data=None):
    # called from menu
    threads_leave()
    c = cue('', update_refs=0)
    editor = cue_edit.cue_editor()
    c.editor = editor
    c.set_editing(1)
    editor.set_cue(c)
    editor.edit()
    threads_enter()
    
class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_cues=0
        self.parent=None
        
    def start_cues (self, attrs):
        self.in_cues = 1

    def end_cues (self):
        self.in_cues = 0
        for c in lb.cue.values():
            c.validate()
    
    def start_instrument (self, attrs):
        if (not self.in_cues): return
        for key, value in attrs.items():
            if key == "name": continue
            self.cue.instrument[attrs['name']]={}
            self.cue.instrument[attrs['name']][key]=value

    def start_cue (self, attrs):
        if (not self.in_cues): return        
        self.cue=cue(attrs['name'])

    def end_cue (self):
        if (not self.in_cues): return        

    def start_parent (self, attrs):
        if (not self.in_cues): return        
        l = attrs['level']
        if l[-1]=='%':
            l=l[:-1]
        l=float(l)
        self.parent=['', l]

    def handle_data (self, data):
        if (not self.in_cues): return        
        if self.parent is not None:
            self.parent[0]=data

    def end_parent (self):
        if (not self.in_cues): return        
        self.cue.parents.append(self.parent)
        self.parent=None

class cue:

    def __init__(self, name, update_refs=1):
        self.instrument={}
        self.apparent={}
        self.valid=0
        self.build_time=0
        self.parents=[]
        self.name=name
        self.core_cue = LB.Cue(name, [])
        self.editor=None
        self.edit_menu_item = None

        if (update_refs):
            self.update_refs()

    def update_refs(self):
        threads_enter()
        try:
            if (lb.cue.has_key(self.name)):
                old = lb.cue[self.name]
                edit_menu.remove(old.edit_menu_item)

            lb.cue[self.name]=self
            
            i=GtkMenuItem(self.name)
            self.edit_menu_item=i
            edit_menu.append(i)
            i.connect("activate", self.edit_cb, None)
            i.show()
        finally:
            threads_leave()

    def has_parent(self, name):
        if (self.name == name):
            return 1
        for (pname, level) in self.parents:
            if (lb.cue[pname].has_parent(name)):
                return 1
        return 0

    def send_update(self):
        s="<cues>\n\n"
        s=s+self.to_xml(1)+"\n"
        s=s+"</cues>\n"
        lb.sendData(s)

    def invalidate(self):
        self.valid = 0
        self.apparent={}
        self.build_time=0
        self.validate()
        
    def validate(self):
        for name, lvl in self.parents:
            lb.cue[name].validate()
            if (lb.cue[name].build_time <= self.build_time):
                continue
            if (self.valid):
                self.apparent={}
                self.valid=0
                self.build_time=0
        for name, lvl in self.parents:
            for name, idict in lb.cue[name].apparent.items():
                if (not self.apparent.has_key(name)):
                    self.apparent[name]={}
                for attr, value in idict.items():
                    if (attr=='level'):
                        value = lb.value_to_string('level', [lb.value_to_core ('level', value)[0] * (lvl/100.0)])
                    self.apparent[name][attr]=value
        if (not self.valid):
            for name, idict in self.instrument.items():
                if (not self.apparent.has_key(name)):
                    self.apparent[name]={}
                for attr, value in idict.items():
                    self.apparent[name][attr]=value
            self.core_cue = self.to_core()
            self.valid=1
            self.build_time=time.time()
        
    def copy(self):
        c = cue(self.name, update_refs=0)
        c.parents=self.parents[:]
        c.instrument=self.instrument.copy()
        c.edit_menu_item = self.edit_menu_item
        c.invalidate()
        return c
    
    def to_core(self):
        incue = self
        cue = LB.Cue(self.name, [])

        for (name, dict) in incue.apparent.items():
            i = lb.instrument[name].to_core_InstAttrs(dict)
            cue.ins = cue.ins + i
        cue.ins=lb.sort_by_attr(cue.ins, 'name')            
        return cue

    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s=s+sp+'<cue name="%s">\n' % self.name
        for name, lvl in self.parents:
            lvl = lb.value_to_string('level', [lvl])
            s=s+sp+'  '+'<parent level="%s">%s</parent>\n' % (lvl, name)
        for name, idict in self.instrument.items():
            l=sp+'  '+'<instrument name="%s"' % name
            for attr, value in idict.items():
                l=l+' %s="%s"' % (attr, value)
            l=l+'/>\n'
            s=s+l
        s=s+sp+'</cue>\n'
        return s

    def edit(self):
        cue = self.copy()
        editor = cue_edit.cue_editor()
        cue.editor = editor
        cue.set_editing(1)
        editor.set_cue(cue)
        editor.edit()

    def edit_cb(self, widget, data):
        """ Called from lightboard->program->edit """

        threads_leave()
        self.edit()
        threads_enter()
        
    def set_editing(self, editing):
        if (editing):
            if (self.edit_menu_item is not None):
                self.edit_menu_item.set_sensitive(0)
        else:
            if (self.edit_menu_item is not None):
                self.edit_menu_item.set_sensitive(1)
            self.editor = None
        
