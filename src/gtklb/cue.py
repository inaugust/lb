from xmllib import XMLParser
from os import path
import string
import lightboard
from ExpatXMLParser import ExpatXMLParser
import operator
from gtk import *
from libglade import *
from completion import completion
import time
import instrument

from omniORB import CORBA
from idl import LB, LB__POA

def initialize(lb):
    lb.cue={}
    try:
        f=open(path.join(lb.datapath, 'cues'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()
        
def shutdown():
    pass

def sort_by_attr(seq, attr):
    intermed = map(None, map(getattr, seq, (attr,)*len(seq)),
                   xrange(len(seq)), seq)
    intermed.sort()
    return map(operator.getitem, intermed, (-1,) * len(intermed))


class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.parent=None
        
    def start_instrument (self, attrs):
        for key, value in attrs.items():
            if key == "name": continue
            self.cue.instrument[attrs['name']]={}
            self.cue.instrument[attrs['name']][key]=value
            print attrs['name'], key, value

    def start_cue (self, attrs):
        self.cue=cue(attrs['name'])

    def end_cue (self):
        lb.cue[self.cue.name]=self.cue
        self.cue.validate()

    def start_parent (self, attrs):
        l = attrs['level']
        if l[-1]=='%':
            l=l[:-1]
        l=float(l)
        self.parent=['', l]

    def handle_data (self, data):
        if self.parent is not None:
            self.parent[0]=data

    def end_parent (self):
        self.cue.parents.append(self.parent)
        self.parent=None

class instrument_cue_proxy:
     def __init__ (self, name, cue):
         # name is the name of the instrument to proxy for
         # cue is the cue object being edited
         self.__dict__['instrument'] = lb.instrument[name]
         self.__dict__['cue'] = cue
         self.__dict__['name'] = name

     def __getattr__(self, name):
         c = self.__dict__['cue']
         n = self.__dict__['name']
         if (c.apparent.has_key(n)):
             if c.apparent[n].has_key(name):
                 return c.apparent[n][name]
         return ''

     def __setattr__(self, name, value):
         c = self.__dict__['cue']
         n = self.__dict__['name']
         i = self.__dict__['instrument']
         value = lb.value_to_string(name, [value])
         if (not c.instrument.has_key(n)):
             c.instrument[n]={}
         if (not c.apparent.has_key(n)):
             c.apparent[n]={}
         c.instrument[n][name]=value
         c.apparent[n][name]=value
         c.build_time=time.time()
         if c.live_updates:
             i.set_attribute(name, value)
         c.update_display()

   

class cue(completion):

    def __init__(self, name):
        self.my_locals={'lb': lb}
        completion.__init__(self, self.my_locals)
        self.instrument={}
        self.apparent={}
        self.valid=0
        self.build_time=0
        self.parents=[]
        self.name=name
        self.core_cue = LB.Cue(name, [])
        self.live_updates=0

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
            self.to_core()
            self.valid=1
            self.build_time=time.time()
        
    def copy(self):
        c = cue(self.name)
        c.parents=self.parents
        c.instrument=self.instrument.copy()
        c.invalidate()
        return c
    
    def to_core(self):
        incue = self
        cue = LB.Cue(self.name, [])

        for (name, dict) in incue.apparent.items():
            i = LB.InstAttrs(name, lb.instrument[name].coreinstrument, [])
            for (attr, value) in dict.items():
                a = LB.AttrValue(lb.core_attr_id(attr),
                                 lb.value_to_core(attr, value))
                i.attrs.append(a)
            i.attrs=sort_by_attr(i.attrs, 'attr')
            cue.ins.append(i)
        cue.ins=sort_by_attr(cue.ins, 'name')            
        return cue

    def update_display(self):
        threads_enter()
        try:
            attrs = ['level']
            ins_in_cue = []
            self.in_tree.clear()
            self.out_tree.clear()
            for name, dict in self.apparent.items():
                l=[name]
                ins_in_cue.append(name)
                for a in attrs:
                    if (dict.has_key(a)):
                        l.append(dict[a])
                    else:
                        l.append('')
                self.in_tree.append (l)
            l = lb.instrument.keys()
            l.sort()
            for name in l:
                if (name not in ins_in_cue):
                    self.out_tree.append([name])
                p = instrument_cue_proxy(name, self)
                self.my_locals[name]=p
        finally:
            threads_leave()


    def edit_add_clicked(self, widget, data=None):
        sel = self.out_tree.selection
        for x in sel:
            # this works whether it's text or pixtext
            name = self.out_tree.get_node_info(x)[0]
            self.instrument[name]={}
            self.apparent[name]={}
        threads_leave()
        self.update_display()
        threads_enter()
    
    def edit_remove_clicked(self, widget, data=None):
        sel = self.in_tree.selection
        for x in sel:
            name = self.in_tree.get_node_info(x)[0]
            try:
                del self.instrument[name]
            except:
                pass
        self.invalidate()
        threads_leave()
        self.update_display()
        threads_enter()

    def edit_updates_clicked(self, widget, data=None):
        active = widget.get_active()
        if (active):
            self.live_updates = 1
            for name, idict in self.apparent.items():
                for attr, value in idict.items():
                    lb.instrument[name].set_attribute(attr, value)
        else:
            self.live_updates = 0
            

    def update_parents_display_help(self, tree, parent_node, level, in_cue):
        level = lb.value_to_string('level', [level])
        if (len(in_cue)):
            if (len (self.parents)): leaf = FALSE
            else: leaf=TRUE
            parent_node=tree.insert_node(parent_node, None, [self.name, level],
                                         is_leaf=leaf)
        in_cue.append(self.name)
        for (name, level) in self.parents:
            in_cue = in_cue + lb.cue[name].update_parents_display_help(tree, parent_node, level, in_cue)
        return in_cue
    
    def update_parents_display(self, node=None):
        threads_enter()

        in_tree=self.parentTree.get_widget("inTree")
        out_tree=self.parentTree.get_widget("outTree")
        try:
            in_tree.clear()
            out_tree.clear()
            parents_in_cue = self.update_parents_display_help(in_tree, None, 0,[])
            l = lb.cue.keys()
            l.sort()
            for name in l:
                if (name not in parents_in_cue):
                    out_tree.append([name])
        finally:
            threads_leave()

    def parent_add_clicked(self, widget, data=None):
        out_tree=self.parentTree.get_widget("outTree")
        sel = out_tree.selection
        for x in sel:
            # this works whether it's text or pixtext
            name = out_tree.get_node_info(x)[0]
            self.parents.append([name, 0.0])
        threads_leave()
        self.update_parents_display()
        threads_enter()
    
    def parent_remove_clicked(self, widget, data=None):
        in_tree=self.parentTree.get_widget("inTree")
        sel = in_tree.selection
        to_remove=[]
        for x in sel:
            name = in_tree.get_node_info(x)[0]
            count = 0
            for p, l in self.parents:
                if p == name:
                    to_remove.append(count)
                    break
                count=count+1
        for i in to_remove:
            del self.parents[i]
        threads_leave()
        self.update_parents_display()
        threads_enter()

    def parent_cancel_clicked(self, widget, data=None):
        self.parents = self.old_parents
        del self.old_parents
        win = self.parentTree.get_widget("cueParent")
        win.destroy()
        
    def parent_ok_clicked(self, widget, data=None):
        del self.old_parents
        win = self.parentTree.get_widget("cueParent")
        win.destroy()

    def parent_level_changed (self, widget, data=None):
        in_tree = self.parentTree.get_widget("inTree")
        node = in_tree.selection[0]
        name = in_tree.node_get_pixtext(node, 0)[0]
        level = self.parent_level_widget.get_string_value()
        in_tree.node_set_text(node, 1, level)
        level = lb.value_to_core('level', level)[0]
        count=0
        for p, l in self.parents:
            if p == name:
                self.parents[count][1]=level
                break
            count=count+1
        
    def parent_row_selected(self, widget, row, column, data=None):
        in_tree = self.parentTree.get_widget("inTree")
        cue_label = self.parentTree.get_widget("cueLabel")
        node = in_tree.node_nth(row)
        name = in_tree.node_get_pixtext(node, 0)[0]
        level = in_tree.node_get_text(node, 1)
        cue_label.set_text(name)
        self.parent_level_widget.set_string_value(level)
            
    def edit_parents(self):
        self.old_parents = self.parents[:]
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "cueParent")
            self.parentTree = wTree

            w=wTree.get_widget ("inTree")
            w.connect ('select_row', self.parent_row_selected)
            t = self.parentTree.get_widget("attributeTable")
            w = lb.attr_widget('level')('0%', self.parent_level_changed)
            t.attach(w.get_widget(), 1,2,1,2)
            self.parent_level_widget = w
            
            b=wTree.get_widget ("add")
            b.connect("clicked", self.parent_add_clicked)
            b=wTree.get_widget ("remove")
            b.connect("clicked", self.parent_remove_clicked)
            b=wTree.get_widget ("cancel")
            b.connect("clicked", self.parent_cancel_clicked)
            b=wTree.get_widget ("ok")
            b.connect("clicked", self.parent_ok_clicked)

            self.parentTree.get_widget("cueParent").show()
            threads_leave()
        #except:
        #    del self.old_parents
        #    threads_leave()
        finally:
            threads_leave()
        self.update_parents_display()
        
    def edit_parents_clicked(self, widget, data=None):
        threads_leave()
        self.edit_parents()
        threads_enter()
    
    def edit_blackout_clicked(self, widget, data=None):
        for name, ins in lb.instrument.items():
            self.instrument[name]={'level': '0%'}
        self.invalidate()
        threads_leave()
        self.update_display()
        threads_enter()
    
    def edit_cancel_clicked(self, widget, data=None):
        win = self.editTree.get_widget("cueEdit")
        win.destroy()

    def edit_ok_clicked(self, widget, data=None):
        win = self.editTree.get_widget("cueEdit")
        lb.cue[self.name]=self
        win.destroy()
            
    def edit(self):
        cue = self.copy()
        cue.edit_self()
        
    def edit_self(self):        
        threads_enter()
        self.locals['self']=self
        try:
            wTree = GladeXML ("gtklb.glade",
                              "cueEdit")
            self.editTree = wTree

            dic = {"on_entry_activate": self.entry_activated,
                   "on_entry_key_press_event": self.key_pressed}
            wTree.signal_autoconnect (dic)

            b=wTree.get_widget ("addToCue")
            b.connect("clicked", self.edit_add_clicked)
            b=wTree.get_widget ("removeFromCue")
            b.connect("clicked", self.edit_remove_clicked)
            b=wTree.get_widget ("liveUpdates")
            b.connect("clicked", self.edit_updates_clicked)
            b=wTree.get_widget ("parents")
            b.connect("clicked", self.edit_parents_clicked)
            b=wTree.get_widget ("blackout")
            b.connect("clicked", self.edit_blackout_clicked)
            b=wTree.get_widget ("cancel")
            b.connect("clicked", self.edit_cancel_clicked)
            b=wTree.get_widget ("ok")
            b.connect("clicked", self.edit_ok_clicked)

            # these three have to be here for the interpreter subclass
            self.textbox = wTree.get_widget ("outputText")
            self.entry = wTree.get_widget ("entry")
            self.more_toggle = wTree.get_widget ("entryMore")

            self.out_tree = wTree.get_widget ("outTree")
            self.in_tree = wTree.get_widget ("inTree")
            self.editTree.get_widget("cueEdit").show()
        finally:
            threads_leave()

        self.update_display()

    def test(self):
        print self.instrument
        print self.apparent

        attrs = ['level']
        for name, dict in self.apparent.items():
            l=[name]
            print name
            for a in attrs:
                if (dict.has_key(a)):
                    l.append(dict[a])
                else:
                    l.append('')
            print l


