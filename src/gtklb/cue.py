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

from omniORB import CORBA
from idl import LB, LB__POA

edit_menu=None

tree_columns=['level', 'color']

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

class cueFactory:
    def __init__(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "nameDialog")
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
            self.tree=wTree
        finally:
            threads_leave()
        
    def ok_clicked(self, widget, data=None):
        w = self.tree.get_widget("nameDialog")
        e = self.tree.get_widget("nameEntry")
        name = e.get_text()
        if not lb.program.has_key(name):
            threads_leave()
            c=cue(name)
            threads_enter()
        w.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.tree.get_widget("nameDialog")
        w.destroy()


def newCue_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = cueFactory()
    threads_enter()
    # that's it.

class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_cues=0
        self.parent=None
        
    def start_cues (self, attrs):
        self.in_cues = 1

    def end_cues (self):
        self.in_cues = 0
        self.cue.validate()
    
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
        if (type(value) != type('')):
            if (type(value) != type([])):
                value = lb.value_to_string(name, [value])
            else:
                value = lb.value_to_string(name, value)
        if (not c.instrument.has_key(n)):
            c.instrument[n]={}
        if (not c.apparent.has_key(n)):
            c.apparent[n]={}
        c.instrument[n][name]=value
        c.apparent[n][name]=value
        c.build_time=time.time()
        if c.live_updates:
            i.set_attribute(name, value)
        c.update_display2(n)
        try:
            c.attribute_widgets[name].set_string_value(value)
        except:
            pass
        

class cue(completion):

    def __init__(self, name, update_refs=1):
        self.my_locals={'lb': lb}
        completion.__init__(self, self.my_locals)
        self.cue_proxies={}
        self.attribute_widgets={}
        self.block_change=0
        self.instrument={}
        self.apparent={}
        self.valid=0
        self.build_time=0
        self.parents=[]
        self.name=name
        self.core_cue = LB.Cue(name, [])
        self.live_updates=0

        if (update_refs):
            self.update_refs()

    def update_refs(self):
        if (lb.cue.has_key(self.name)):
            old = lb.cue[self.name]
            edit_menu.remove(old.edit_menu_item)
        lb.cue[self.name]=self
            
        threads_enter()
        try:
            i=GtkMenuItem(self.name)
            self.edit_menu_item=i
            edit_menu.append(i)
            i.connect("activate", self.edit_cb, None)
            i.show()
        finally:
            threads_leave()

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
        c = cue(self.name, update_refs=0)
        c.parents=self.parents
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

    def update_display2(self, name):
        """just update it"""
        dict=self.apparent[name]
        row = self.in_tree.find_row_from_data(self.cue_proxies[name])
        if (row<0):
            l=[name]
            for a in tree_columns:
                if (dict.has_key(a)):
                    l.append(dict[a])
                else:
                    l.append('')
            pos = self.in_tree.append (l)
            node = self.in_tree.node_nth(pos)
            self.in_tree.node_set_row_data(node, self.cue_proxies[name])
            return
        
        col = 1
        for a in tree_columns:
            if (dict.has_key(a)):
                self.in_tree.set_text(row, col, dict[a])
            else:
                self.in_tree.set_text(row, col, '')
            col = col + 1

    def update_display(self):
        """should be called redraw"""
        threads_enter()
        try:
            ins_in_cue = []
            self.in_tree.clear()
            self.out_tree.clear()
            for name, dict in self.apparent.items():
                l=[name]
                ins_in_cue.append(name)
                for a in tree_columns:
                    if (dict.has_key(a)):
                        l.append(dict[a])
                    else:
                        l.append('')
                pos = self.in_tree.append (l)
                node = self.in_tree.node_nth(pos)
                self.in_tree.node_set_row_data(node, self.cue_proxies[name])
            l = lb.instrument.keys()
            l.sort()
            for name in l:
                if (name not in ins_in_cue):
                    self.out_tree.append([name])
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
        threads_leave()
        self.update_refs()
        threads_enter()
        win.destroy()

    def edit_attr_changed(self, widget, data=None):
        n = self.editing_instrument

        name = widget.attribute
        value = widget.get_string_value()
        if (not self.instrument.has_key(n)):
            self.instrument[n]={}
        if (not self.apparent.has_key(n)):
            self.apparent[n]={}
        self.instrument[n][name]=value
        self.apparent[n][name]=value
        self.build_time=time.time()
        if self.live_updates:
            lb.instrument[n].set_attribute(name, value)
        self.update_display2(n)
        
    def edit_row_selected(self, widget, row, column, data=None):
        in_tree = self.editTree.get_widget("inTree")
        table = self.editTree.get_widget("attributeTable")
        node = in_tree.node_nth(row)
        #node = in_tree.selection[0]
        name = in_tree.node_get_pixtext(node, 0)[0]
        
        for c in table.children():
            table.remove(c)

        ins =lb.instrument[name]
        self.editing_instrument=name

        l = len (ins.attributes)
        table.resize(2, l+1)

        w = GtkLabel("Instrument:")
        table.attach(w, 0,1,0,1, xoptions=FILL, yoptions=0)
        w = GtkLabel(name)
        align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
        align.add(w)
        table.attach(align, 1,2,0,1, xoptions=FILL, yoptions=0)

        for i in range(1,l+1):
            a = ins.attributes[i-1]
            v = getattr(self.locals[self.editing_instrument], a)
            w = GtkLabel(a)
            table.attach(w, 0,1, i,i+1, xoptions=FILL, yoptions=0)
            w = lb.attr_widget(a)(v, self.edit_attr_changed)            
            self.attribute_widgets[a]=w
            align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
            align.add(w.get_widget())
            table.attach(align, 1,2, i,i+1, xoptions=FILL, yoptions=0)
        table.show_all()
        return 1

    def edit_row_unselected(self, widget, row, column, data=None):
        self.editing_instrument=None
        table = self.editTree.get_widget("attributeTable")
        
        for c in table.children():
            table.remove(c)
           
    def edit(self):
        cue = self.copy()
        cue.edit_self()

    def edit_destroyed(self, widget, data=None):
        self.edit_menu_item.set_sensitive(1)        

    def edit_cb(self, widget, data):
        """ Called from lightboard->program->edit """

        self.edit_menu_item.set_sensitive(0)
        threads_leave()
        self.edit()
        threads_enter()
        
    def edit_self(self):        
        self.locals['self']=self
        l = lb.instrument.keys()
        for name in l:
            p = instrument_cue_proxy(name, self)
            self.my_locals[name]=p
            self.cue_proxies[name]=p

        threads_enter()
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
            w=wTree.get_widget("cueEdit")
            w.connect ('destroy', self.edit_destroyed)
            w.set_title ('Edit Cue %s' % self.name)
            
            self.in_tree.connect ('select-row', self.edit_row_selected)
            self.in_tree.connect ('unselect-row', self.edit_row_unselected)
        finally:
            threads_leave()

        self.update_display()

