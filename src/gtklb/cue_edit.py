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
import cue

from omniORB import CORBA
from idl import LB, LB__POA

tree_columns=['level', 'color', 'gobo_rpm']

class defunct_instrument_cue_proxy:
    def __init__ (self, name):
        self.__dict__['name'] = name

    def get_name (self):
        return self.__dict__['name']

    def __getattr__(self, name):
        return ''

    def __setattr__(self, name, value):
        pass

class instrument_cue_proxy:
    def __init__ (self, name, editor):
        # name is the name of the instrument to proxy for
        # editor is the editor containing this
        self.__dict__['instrument'] = lb.instrument[name]
        self.__dict__['editor'] = editor
        self.__dict__['name'] = name

    def get_name (self):
        return self.__dict__['name']

    def __getattr__(self, name):
        e = self.__dict__['editor']
        n = self.__dict__['name']
        if (e.cue.apparent.has_key(n)):
            if e.cue.apparent[n].has_key(name):
                return e.cue.apparent[n][name]
        return ''

    def __setattr__(self, name, value):
        e = self.__dict__['editor']
        n = self.__dict__['name']
        i = self.__dict__['instrument']
        if (type(value) != type('')):
            if (type(value) != type([])):
                value = lb.value_to_string(name, [value])
            else:
                value = lb.value_to_string(name, value)
        if (not e.cue.instrument.has_key(n)):
            e.cue.instrument[n]={}
        if (not e.cue.apparent.has_key(n)):
            e.cue.apparent[n]={}
        e.cue.instrument[n][name]=value
        e.cue.apparent[n][name]=value
        e.cue.build_time=time.time()
        if e.live_updates:
            i.set_attribute(name, value)
        e.update_display2(n)
        try:
            e.attribute_widgets[name].set_string_value(value)
        except:
            pass
        

class CueEditor(completion):

    def __init__(self):
        self.my_locals={'lb': lb}
        completion.__init__(self, self.my_locals)
        self.cue_proxies={}
        self.attribute_widgets={}
        self.live_updates=0
        self.cue = None
        self.initialized = 0
        self.child_windows=[]
        self.cue_menu_handler_id = None

    def set_cue (self, cue, reinit = 0, update_menu = 1):
        if (not reinit):
            self.cue = cue

        if not self.initialized or self.cue is None:
            return
        
        for w in self.child_windows:
            w.destroy()

        self.child_windows = []
        self.editing_instruments = []
        self.locals['self']=self.cue

        self.editTree.get_widget ("nameEntry").set_text(self.cue.name)
        if (self.cue.name != ''):
            self.editTree.get_widget ("nameEntry").set_sensitive(0)
            b = self.editTree.get_widget('ok').set_sensitive(1)
            b = self.editTree.get_widget('save').set_sensitive(1)
        else:
            self.editTree.get_widget ("nameEntry").set_sensitive(1)
            b = self.editTree.get_widget('ok').set_sensitive(0)
            b = self.editTree.get_widget('save').set_sensitive(0)            

        w=self.editTree.get_widget("cueEdit")
        w.set_title ('Edit Cue %s' % self.cue.name)
        if (update_menu):
            self.update_cue_menu()
            
    def update_display2(self, name):
        """just update it"""
        in_tree = self.editTree.get_widget("inTree")
        dict=self.cue.apparent[name]
        row = in_tree.find_row_from_data(self.cue_proxies[name])

        defunct = 0
        try: proxy = self.cue_proxies[name]
        except:
            proxy = defunct_instrument_cue_proxy(name)
            name = name + " <defunct>"
            defunct = 1
        if not self.cue.instrument.has_key (name) and not defunct:
            name = name + " <inherited>"

        if (row<0):
            l=[name]
            for a in tree_columns:
                if (dict.has_key(a)):
                    l.append(dict[a])
                else:
                    l.append('')
            pos = in_tree.append (l)
            node = in_tree.node_nth(pos)
            in_tree.node_set_row_data(node, proxy)
            return
        
        col = 1
        in_tree.set_text(row, 0, name)
        for a in tree_columns:
            if (dict.has_key(a)):
                in_tree.set_text(row, col, dict[a])
            else:
                in_tree.set_text(row, col, '')
            col = col + 1

    def update_display(self):
        """should be called redraw"""
        threads_enter()
        in_tree = self.editTree.get_widget("inTree")
        out_tree = self.editTree.get_widget("outTree")
        try:
            ins_in_cue = []
            in_tree.clear()
            out_tree.clear()
            groups_in_in = {}
            for name, dict in self.cue.apparent.items():
                origname = name
                defunct = 0
                try: proxy = self.cue_proxies[name]
                except:
                    proxy = defunct_instrument_cue_proxy(name)
                    name = name + " <defunct>"
                    defunct = 1
                if not defunct:
                    group = lb.instrument[name].group
                if not self.cue.instrument.has_key (name) and not defunct:
                    name = name + " <inherited>"
                l=[name]
                ins_in_cue.append(origname)
                for a in tree_columns:
                    if (dict.has_key(a)):
                        l.append(dict[a])
                    else:
                        l.append('')

                parent = None
                if group is not None:
                    try: parent = groups_in_in[group]
                    except:
                        gl = [group]
                        for a in tree_columns:
                            gl.append('')
                        parent = in_tree.insert_node(None, None, gl, is_leaf=FALSE)
                        groups_in_in[group]=parent

                node = in_tree.insert_node(parent, None, l, is_leaf=TRUE)
                in_tree.node_set_row_data(node, proxy)
            l = lb.instrument_group.keys()
            l.sort()
            for name in l:
                parent = None
                if name is not None:
                    parent = out_tree.insert_node(None, None, [name], is_leaf=FALSE)
                l2 = lb.instrument_group[name].keys()
                l2.sort()
                for name2 in l2:
                    if (name2 not in ins_in_cue):
                        out_tree.insert_node(parent, None, [name2], is_leaf=TRUE)
                        
        finally:
            threads_leave()


    def edit_add_clicked(self, widget, data=None):
        out_tree = self.editTree.get_widget("outTree")
        sel = out_tree.selection
        for x in sel:
            info = out_tree.get_node_info(x)
            leaf = info[6]
            if not leaf:
                continue
            name = info[0]
            self.cue.instrument[name]={}
            self.cue.apparent[name]={}
        threads_leave()
        self.update_display()
        threads_enter()
    
    def edit_remove_clicked(self, widget, data=None):
        in_tree = self.editTree.get_widget("inTree")
        sel = in_tree.selection
        for x in sel:
            data = in_tree.node_get_row_data(x)
            name = data.get_name()
            try:
                del self.cue.instrument[name]
            except:
                pass
        self.cue.invalidate()
        threads_leave()
        self.update_display()
        threads_enter()
        self.edit_row_selection_changed(None, None, None)

    def edit_updates_clicked(self, widget, data=None):
        active = widget.get_active()
        if (active):
            self.live_updates = 1
            for name, idict in self.cue.apparent.items():
                for attr, value in idict.items():
                    lb.instrument[name].set_attribute(attr, value)
        else:
            self.live_updates = 0
            
    def update_parents_display_help(self, cue, tree, parent_node, level, in_cue):
        level = lb.value_to_string('level', [level])
        if (len(in_cue)):
            if (len (cue.parent)): leaf = FALSE
            else: leaf=TRUE
            parent_node=tree.insert_node(parent_node, None, [cue.name,
                                                             level],
                                         is_leaf=leaf)
        in_cue.append(cue.name)
        for (name, level) in cue.parent:
            in_cue = in_cue + self.update_parents_display_help(lb.cue[name], tree, parent_node, level, in_cue)
        return in_cue
    
    def update_parents_display(self, node=None):
        threads_enter()

        in_tree=self.parentTree.get_widget("inTree")
        out_tree=self.parentTree.get_widget("outTree")
        try:
            in_tree.clear()
            out_tree.clear()
            parents_in_cue = self.update_parents_display_help(self.cue, in_tree, None, 0,[])
            l = lb.cue.keys()
            l.sort()
            for name in l:
                if (name not in parents_in_cue):
                    if (not lb.cue[name].has_parent(self.cue.name)):
                        out_tree.append([name])
        finally:
            threads_leave()

    def parent_add_clicked(self, widget, data=None):
        out_tree=self.parentTree.get_widget("outTree")
        sel = out_tree.selection
        for x in sel:
            # this works whether it's text or pixtext
            name = out_tree.get_node_info(x)[0]
            self.cue.parent.append([name, 0.0])
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
            for p, l in self.cue.parent:
                if p == name:
                    to_remove.append(count)
                    break
                count=count+1
        for i in to_remove:
            del self.cue.parent[i]
        threads_leave()
        self.update_parents_display()
        threads_enter()

    def parent_destroyed(self, widget, data=None):
        win = self.parentTree.get_widget("cueParent")
        self.child_windows.remove(win)
        if (self.cues_old_parents is not None):
            self.cue.parent = self.cues_old_parents
        del self.cues_old_parents

    def parent_cancel_clicked(self, widget, data=None):
        win = self.parentTree.get_widget("cueParent")
        win.destroy()
        
    def parent_ok_clicked(self, widget, data=None):
        self.cues_old_parents = None
        win = self.parentTree.get_widget("cueParent")
        win.destroy()
        self.cue.invalidate()
        threads_leave()
        self.update_display()
        threads_enter()
        
    def parent_level_changed (self, widget, data=None):
        in_tree = self.parentTree.get_widget("inTree")
        node = in_tree.selection[0]
        name = in_tree.node_get_pixtext(node, 0)[0]
        level = self.parent_level_widget.get_string_value()
        in_tree.node_set_text(node, 1, level)
        level = lb.value_to_core('level', level)[0]
        count=0
        for p, l in self.cue.parent:
            if p == name:
                self.cue.parent[count][1]=level
                break
            count=count+1
        if self.live_updates:
            self.cue.invalidate()
            for name, idict in self.cue.apparent.items():
                for attr, value in idict.items():
                    lb.instrument[name].set_attribute(attr, value)
            threads_leave()
            self.update_display()
            threads_enter()
        
    def parent_row_selected(self, widget, row, column, data=None):
        in_tree = self.parentTree.get_widget("inTree")
        cue_label = self.parentTree.get_widget("cueLabel")
        node = in_tree.node_nth(row)
        if (node.parent is None):
            name = in_tree.node_get_pixtext(node, 0)[0]
            level = in_tree.node_get_text(node, 1)
            cue_label.set_text(name)
            self.parent_level_widget.set_string_value(level)
            self.parent_level_widget.get_widget().set_sensitive(1)
        else:
            cue_label = self.parentTree.get_widget("cueLabel")
            cue_label.set_text('')
            self.parent_level_widget.get_widget().set_sensitive(0)
        return 1
    
    def parent_row_unselected(self, widget, row, column, data=None):
        self.parent_level_widget.get_widget().set_sensitive(0)
        cue_label = self.parentTree.get_widget("cueLabel")
        cue_label.set_text('')
        return 1
        
    def edit_parents(self):
        self.cues_old_parents = self.cue.parent[:]
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "cueParent")
            self.parentTree = wTree

            w=wTree.get_widget ("inTree")
            w.connect ('select_row', self.parent_row_selected)
            w.connect ('unselect_row', self.parent_row_unselected)
            t = self.parentTree.get_widget("attributeTable")
            w = lb.attr_widget('level')('0%', self.parent_level_changed)
            t.attach(w.get_widget(), 1,2,1,2)
            self.parent_level_widget = w
            w.get_widget().set_sensitive(0)
            
            b=wTree.get_widget ("add")
            b.connect("clicked", self.parent_add_clicked)
            b=wTree.get_widget ("remove")
            b.connect("clicked", self.parent_remove_clicked)
            b=wTree.get_widget ("cancel")
            b.connect("clicked", self.parent_cancel_clicked)
            b=wTree.get_widget ("ok")
            b.connect("clicked", self.parent_ok_clicked)

            win = self.parentTree.get_widget("cueParent")
            win.connect("destroy", self.parent_destroyed)
        finally:
            threads_leave()
        self.update_parents_display()
        return win
        
    def edit_parents_clicked(self, widget, data=None):
        threads_leave()
        self.child_windows.append(self.edit_parents())
        threads_enter()
    
    def edit_blackout_clicked(self, widget, data=None):
        for name, ins in lb.instrument.items():
            self.cue.instrument[name]={'level': '0%'}
        self.cue.invalidate()
        threads_leave()
        self.update_display()
        threads_enter()
    
    def edit_cancel_clicked(self, widget, data=None):
        win = self.editTree.get_widget("cueEdit")
        win.destroy()

    def edit_new_clicked(self, widget, data=None):
        self.cue.set_editing(0)
        newcue = cue.Cue('', update_refs = 0)
        newcue.editor=self
        self.set_cue(newcue)
        threads_leave()
        self.update_display()
        threads_enter()
        
    def do_save_actions(self):
        threads_leave()
        self.cue.invalidate()
        self.cue.update_refs()
        self.cue.send_update()
        for c in lb.cue.values():
            c.validate()
        threads_enter()
        self.editTree.get_widget ("nameEntry").set_sensitive(0)
        self.update_cue_menu()
        self.cue.set_editing(1)
        
    def edit_save_clicked(self, widget, data=None):
        self.do_save_actions()
        self.set_cue(lb.cue[self.cue.name].copy())
            
    def edit_ok_clicked(self, widget, data=None):
        win = self.editTree.get_widget("cueEdit")
        self.do_save_actions()
        self.cue.set_editing(0)
        win.destroy()
    
    def edit_revert_clicked(self, widget, data=None):
        if lb.cue.has_key(self.cue.name):
            self.set_cue(lb.cue[self.cue.name].copy())
        else:
            self.cue.set_editing(0)
            newcue = cue.Cue('', update_refs = 0)
            newcue.editor=self
            self.set_cue(newcue)
        threads_leave()
        self.update_display()
        threads_enter()

    def nameEntry_changed(self, widget, event=None, data=None):
        s = widget.get_text()
        if (s!='' and (not lb.cue.has_key(s))):
            self.cue.name = s
            b = self.editTree.get_widget('ok')
            b.set_sensitive(1)
            b = self.editTree.get_widget('save')
            b.set_sensitive(1)            
        else:
            b = self.editTree.get_widget('ok')
            b.set_sensitive(0)
            b = self.editTree.get_widget('save')
            b.set_sensitive(0)            
        
    def edit_attr_changed(self, widget, data=None):
        name = widget.attribute
        value = widget.get_string_value()
        
        for n in self.editing_instruments:
            if (not self.cue.instrument.has_key(n)):
                self.cue.instrument[n]={}
            if (not self.cue.apparent.has_key(n)):
                self.cue.apparent[n]={}
            self.cue.instrument[n][name]=value
            self.cue.apparent[n][name]=value
            self.cue.build_time=time.time()
            if self.live_updates:
                lb.instrument[n].set_attribute(name, value)
            self.update_display2(n)

    def edit_update_attribute_widgets(self):
        table = self.editTree.get_widget("attributeTable")
        for c in table.children():
            table.remove(c)

        if (len (self.editing_instruments) == 0):
            return

        try:
            common_attrs = list(lb.instrument[self.editing_instruments[0]].attributes)
        except:  # defunct instrument
            return
        
        for n in self.editing_instruments:
            i =lb.instrument[n]
            for a in common_attrs:
                if a not in i.attributes:
                    common_attrs.remove(a)

        l = len (common_attrs)
        table.resize(2, l+1)

        w = GtkLabel("Instrument:")
        table.attach(w, 0,1,0,1, xoptions=FILL, yoptions=0)
        s = self.editing_instruments[0]
        for n in self.editing_instruments[1:]:
            s=s+", "+n
        w = GtkLabel(s)
        align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
        align.add(w)
        table.attach(align, 1,2,0,1, xoptions=FILL, yoptions=0)

        for i in range(1,l+1):
            a = common_attrs[i-1]
            v = getattr(self.cue_proxies[self.editing_instruments[0]], a)
            w = GtkLabel(a)
            table.attach(w, 0,1, i,i+1, xoptions=FILL, yoptions=0)
            w = lb.attr_widget(a)(v, self.edit_attr_changed)            
            self.attribute_widgets[a]=w
            align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
            align.add(w.get_widget())
            table.attach(align, 1,2, i,i+1, xoptions=FILL, yoptions=0)
        table.show_all()
        
    def edit_row_selection_changed(self, widget, node, data=None):
        in_tree = self.editTree.get_widget("inTree")
        table = self.editTree.get_widget("attributeTable")
        self.editing_instruments=[]
        for n in in_tree.selection:
            data = in_tree.node_get_row_data(n)
            if data is None:
                continue
            name = data.get_name()
            self.editing_instruments.append(name)
        self.edit_update_attribute_widgets()
        return 1
    
    def edit_destroyed(self, widget, data=None):
        self.cue.set_editing(0)
        for w in self.child_windows:
            w.destroy()

    def cue_changed(self, widget, data=None):
        menu = self.editTree.get_widget("cueMenu")
        name = menu.entry.get_text()
        newcue = lb.cue[name].copy()
        self.cue.set_editing(0)
        newcue.editor=self
        self.set_cue(newcue, update_menu=0)
        threads_leave()
        self.update_display()
        threads_enter()

    def update_cue_menu(self):
        combo = self.editTree.get_widget("cueMenu")
        if self.cue_menu_handler_id is not None:
            combo.entry.disconnect (self.cue_menu_handler_id)
        entries = lb.cue.keys()[:]
        if entries:
            combo.set_popdown_strings(entries)
        combo.entry.set_text(self.cue.name)
        self.cue_menu_handler_id = combo.entry.connect ("changed", self.cue_changed, None)
        
    def edit(self):        
        if (self.initialized):
            return
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
                   "on_entry_key_press_event": self.key_pressed,
                   "on_nameEntry_changed": self.nameEntry_changed,
                   "on_addToCue_clicked": self.edit_add_clicked,
                   "on_removeFromCue_clicked": self.edit_remove_clicked,
                   "on_liveUpdates_clicked": self.edit_updates_clicked,
                   "on_parents_clicked": self.edit_parents_clicked,
                   "on_blackout_clicked": self.edit_blackout_clicked,
                   "on_new_clicked": self.edit_new_clicked,
                   "on_save_clicked": self.edit_save_clicked,
                   "on_revert_clicked": self.edit_revert_clicked,
                   "on_cancel_clicked": self.edit_cancel_clicked,
                   "on_ok_clicked": self.edit_ok_clicked
                   }

            wTree.signal_autoconnect (dic)

            # these three have to be here for the interpreter subclass
            self.textbox = wTree.get_widget ("outputText")
            self.entry = wTree.get_widget ("entry")
            self.more_toggle = wTree.get_widget ("entryMore")

            in_tree = wTree.get_widget ("inTree")
            in_tree.connect ('tree_select_row',
                             self.edit_row_selection_changed)
            in_tree.connect ('tree_unselect_row',
                             self.edit_row_selection_changed)
            w=wTree.get_widget("cueEdit")
            w.connect ('destroy', self.edit_destroyed)

            self.initialized = 1
            self.set_cue(self.cue, reinit=1)
        finally:
            threads_leave()

        self.update_display()

