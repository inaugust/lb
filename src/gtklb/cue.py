from xmllib import XMLParser
from os import path
import string
import lightboard
from ExpatXMLParser import ExpatXMLParser, DOMNode
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

def load(tree):
    for section in tree.find("cues"):
        for cue in section.find("cue"):
            c=Cue(cue.attrs['name'])
            for parent in cue.find("parent"):
                l = parent.attrs['level']
                if l[-1]=='%':
                    l=l[:-1]
                l=float(l)
                c.parent.append([string.strip(parent.data), l])
            for instrument in cue.find("instrument"):
                for key, value in instrument.attrs.items():
                    if key == "name": continue
                    if not c.instrument.has_key(instrument.attrs['name']):
                        c.instrument[instrument.attrs['name']]={}
                    c.instrument[instrument.attrs['name']][key]=value

    for c in lb.cue.values():
        c.validate()
    
def save():
    tree = DOMNode('cues')
    for i in lb.cue.values():
        tree.append(i.to_tree())
    return tree

def newCue_cb(widget, data=None):
    # called from menu
    threads_leave()
    c = Cue('', update_refs=0)
    editor = cue_edit.CueEditor()
    c.editor = editor
    c.set_editing(1)
    editor.set_cue(c)
    editor.edit()
    threads_enter()
    

class Cue:
    def __init__(self, name, update_refs=1):
        self.instrument={}
        self.apparent={}
        self.valid=0
        self.build_time=0
        self.parent=[]
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
        for (pname, level) in self.parent:
            if (lb.cue[pname].has_parent(name)):
                return 1
        return 0

    def send_update(self):
        tree = DOMNode('cues')
        tree.append(self.to_tree())
        lb.sendData(tree)

    def invalidate(self):
        self.valid = 0
        self.apparent={}
        self.build_time=0
        self.validate()
        
    def validate(self):
        for name, lvl in self.parent:
            lb.cue[name].validate()
            if (lb.cue[name].build_time <= self.build_time):
                continue
            if (self.valid):
                self.apparent={}
                self.valid=0
                self.build_time=0
        if (not self.valid):
            for name, lvl in self.parent:
                for name, idict in lb.cue[name].apparent.items():
                    if (not self.apparent.has_key(name)):
                        self.apparent[name]={}
                    for attr, value in idict.items():
                        if (attr=='level'):
                            value = lb.value_to_string('level', [lb.value_to_core ('level', value)[0] * (lvl/100.0)])
                        self.apparent[name][attr]=value
            for name, idict in self.instrument.items():
                if (not self.apparent.has_key(name)):
                    self.apparent[name]={}
                for attr, value in idict.items():
                    self.apparent[name][attr]=value
            self.core_cue = self.to_core()
            self.valid=1
            self.build_time=time.time()
        
    def copy(self):
        c = Cue(self.name, update_refs=0)
        c.parent=self.parent[:]
        c.instrument=self.instrument.copy()
        c.edit_menu_item = self.edit_menu_item
        c.invalidate()
        return c
    
    def to_core(self):
        incue = self
        cue = LB.Cue(self.name, [])

        for (name, dict) in incue.apparent.items():
            try:
                i = lb.instrument[name].to_core_InstAttrs(dict)
                cue.ins = cue.ins + i
            except:
                pass
        cue.ins=lb.sort_by_attr(cue.ins, 'name')            
        return cue

    def to_tree(self):
        cue = DOMNode('cue', {'name':self.name})
        for name, lvl in self.parent:
            lvl = lb.value_to_string('level', [lvl])
            parent = DOMNode('parent', {'level':lvl})
            parent.add_data(name)
            cue.append(parent)
        for name, idict in self.instrument.items():
            dict = idict.copy()
            dict['name']=name
            instrument = DOMNode('instrument', dict)
            cue.append(instrument)
        return cue

    def edit(self):
        cue = self.copy()
        editor = cue_edit.CueEditor()
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
        
