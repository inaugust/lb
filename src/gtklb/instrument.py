from os import path
import lightboard
import time
from gtk import *
import GDK
from libglade import *
import attribute_widgets

from ExpatXMLParser import ExpatXMLParser, DOMNode
from idl import LB

def initialize():
    lb.instrument_module_info = {}
    lb.instrument_module_info['Instrument'] = instrument_info
    reset()
    
def reset():
    lb.instrument={}
    lb.instrument_group={}
    lb.instrument_group[None]={}

    threads_enter()
    menubar=lb.menubar
    for m in menubar.children():
        if (m.children()[0].get() == "Instrument"):
            menubar.remove(m)

    program1=GtkMenuItem("Instrument")
    menubar.append(program1)

    program1_menu=GtkMenu()
    program1.set_submenu(program1_menu)

    new1=GtkMenuItem("Edit")
    new1.connect("activate", editInstrument_cb, None)
    program1_menu.append(new1)

    menubar.show_all()
    threads_leave()

def shutdown():
    pass

def delete_help(parent, group = None):
    for ins in parent.children:
        delete_help(ins, group)
    try: del lb.instrument[parent.attrs['name']]
    except: pass
    try: del lb.instrument_group[group][parent.attrs['name']]
    except: pass
    try:
        if len (lb.instrument_group[group]) == 0 and group is not None:
            del lb.instrument_group[group]
    except: pass        

def load_clump (tree, group = None):
    for ins in tree.find("instrument"):
        i=Instrument(ins.attrs, group)
    
def load(tree):
    for section in tree.find("instruments"):
        load_clump(section)
        for group in section.find("group"):
            load_clump(group, group.attrs['name'])
    
    for section in tree.find("instruments-deleted"):
        for ins in section.children:
            delete_help(ins)
        for group in section.find("group"):
            for ins in group.children:
                delete_help(ins, group.attrs['name'])
                
def save():
    tree = DOMNode('instruments')
    for name, dict in lb.instrument_group.items():
        if name is None:
            n = tree
        else:
            n = DOMNode('group', {'name': name})
            tree.append(n)
        for i in dict.values():
            n.append(i.to_tree())
    return tree

def editInstrument_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = InstrumentEditor()
    threads_enter()
    # that's it.


class Instrument:

    attributes=('level',)
    module='instrument'

    def __init__(self, args, group = None, hidden = 0):
        self.name = args['name']
        self.driver = args['driver']
        self.corename = args['core']
        print self.name, self.driver, self.corename
        self.parent = None
        self.group = group
        self.hidden = hidden

        self.arglist = []
        for n,v in args.items():
            if n in ('name', 'driver', 'core'):
                continue
            self.arglist.append(LB.Argument(n,v))

        self.coreinstrument=lb.get_instrument(self.name)
        if (self.coreinstrument is not None):
            e=0
            try:
                e=self.coreinstrument._non_existent()
            except:
                self.coreinstrument=None
            if (e): self.coreinstrument=None
        if (self.coreinstrument is None):
            #print "I'm here!\n"
            c = lb.get_core(self.corename)
            c.createInstrument (lb.show, self.name, self.driver, self.arglist)
            self.coreinstrument=lb.get_instrument(self.name)

        attrlist = []
        for attr in self.coreinstrument.getAttributes():
            for (name, t) in attribute_widgets.attribute_mapping.items():
                if t[0] == attr:
                    attrlist.append(name)
        self.attributes = tuple(attrlist)
        
        if not hidden:
            if group is not None:
                if not lb.instrument_group.has_key(group):
                    lb.instrument_group[group]={}
                lb.instrument_group[group][self.name]=self
            else:
                lb.instrument_group[None][self.name]=self
        lb.instrument[self.name]=self

        
    #public

    def to_tree(self):
        dict = {}
        for arg in self.arglist:
            dict[arg.name]=arg.value
            
        dict['name']=self.name
        dict['driver']=self.driver
        dict['core']=self.corename

        instrument = DOMNode(self.module, dict)
        return instrument

    def get_attribute (self, name):
        if name == 'level': return self.get_level()
        if name == 'gobo_rpm': return self.get_gobo_rpm()            
        raise AttributeError, name
    
    def set_attribute (self, name, arg):
        if name == 'level': return self.set_level(arg)
        if name == 'gobo_rpm': return self.set_gobo_rpm(arg)
        raise AttributeError, name
        
    def set_level (self, level):
        self.coreinstrument.setLevel (lb.value_to_core('level', level)[0])

    def get_level (self):
        return lb.value_to_string('level', [self.coreinstrument.getLevel ()])

    def set_gobo_rpm (self, rpm):
        self.coreinstrument.setGoboRPM (lb.value_to_core('gobo_rpm', rpm)[0])

    def get_gobo_rpm (self):
        return lb.value_to_string('gobo_rpm', [self.coreinstrument.getGoboRPM ()])

    def to_core_InstAttrs (self, attr_dict):
        """ Used by Cues to create a core cue.  But note how easily it
        can be overridden to return a list of several InstAttrs,
        so that you can have a kind of Meta-Instrument that controls more
        than one actual instrument. """
        
        i = LB.InstAttrs(self.name, self.coreinstrument, [])
        for (attr, value) in attr_dict.items():
            a = LB.AttrValue(lb.core_attr_id(attr),
                             lb.value_to_core(attr, value))
            i.attrs.append(a)
        i.attrs=lb.sort_by_attr(i.attrs, 'attr')
        return [i]


def get_core_names(attrs):
    lb.check_cores()
    return lb.core_names
        
class InstrumentInfo:
    container = 0
    module = 'instrument'
    clazz = Instrument

    def load(self, tree):
        load(tree)

    def get_arguments(self, ins):
        dict = {'name': ['', ''],
                'driver': ['', lambda attrs: lb.get_core(attrs['core'][0]).enumerateDrivers()],
                           
                'core':['', get_core_names]
                }

        if not ins.attrs.has_key('core'):
            ins.attrs['core']=get_core_names(None)[0]
        if not ins.attrs.has_key('driver'):
            ins.attrs['driver']=lb.get_core(ins.attrs['core']).enumerateDrivers()[0]
        l = lb.get_core(ins.attrs['core']).enumerateDriverArguments(ins.attrs['driver'])
        for a in l:
            dict[a]=['','']
        for name, value in dict.items():
            if ins.attrs.has_key(name):
                dict[name][0]=ins.attrs[name]
        return dict

    def get_arguments_for_children(self, ins):
        return {}

class GroupInfo:
    container = 1
    module = 'group'
    clazz = None
    allowable_children = ['*']
    
    def load(self, tree):
        pass

    def get_arguments(self, ins):
        dict = {'name': ['', '']}

        for name, value in dict.items():
            if ins.attrs.has_key(name):
                dict[name][0]=ins.attrs[name]
        return dict

    def get_arguments_for_children(self, ins):
        return {}

instrument_info = InstrumentInfo()
group_info = GroupInfo()

def do_insertion(tree, parent, ins):
    for i in ins.children:
        found = 0
        if i.tag == 'group':
            node = tree.insert_node(parent, None, [i.attrs['name']], is_leaf=FALSE)
            do_insertion(tree, node, i)
            tree.node_set_row_data(node, (i,group_info))
            continue
        for m in lb.instrument_module_info.values():
            if i.tag == m.module:
                found = 1
                if m.container:
                    node = tree.insert_node(parent, None, [i.attrs['name']], is_leaf=FALSE)
                    do_insertion(tree, node, i)
                else:
                    node = tree.insert_node(parent, None, [i.attrs['name']], is_leaf=TRUE)
                tree.node_set_row_data(node, (i,m))
            if found: break
    

    
class InstrumentEditor:
   
    def __init__(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "editInstruments")
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked,
                   "on_add_clicked": self.add_clicked,
                   "on_addGroup_clicked": self.add_group_clicked,
                   "on_remove_clicked": self.remove_clicked,
                   }
            
            wTree.signal_autoconnect (dic)

            tree = wTree.get_widget("instrumentTree")
            tree.set_reorderable(1)
            tree.connect ('select_row', self.row_selected)
            tree.connect ('unselect_row', self.row_unselected)
            tree.set_drag_compare_func(self.drag_compare)

            menu = GtkMenu()
            i=GtkMenuItem("Delete")
            i.connect("activate", self.popup_delete_activated, None)
            menu.append(i)
            menu.show_all()
            self.popup_menu = menu
            tree.connect("button_press_event", self.popup_handler)
            
            self.oldSelection = None

            ins = save()
            do_insertion(tree, None, ins)
            
            optionMenu = wTree.get_widget("driverMenu")
            menu=GtkMenu()
            mods = lb.instrument_module_info.keys()
            mods.sort()
            for m in mods:
                i=GtkMenuItem(m)
                i.show()
                menu.append(i)
            menu.show_all()
            optionMenu.set_menu(menu)
            optionMenu.set_history(0)
            menu.show()

            self.editTree=wTree
        finally:
            threads_leave()

    def drag_compare(self, source, parent, sibling):
        if (parent is None):
            return 1
        tree = self.editTree.get_widget("instrumentTree")
        data = tree.node_get_row_data(parent)
        dest_info = data[1]
        data = tree.node_get_row_data(source)
        source_info = data[1]        
        if hasattr(dest_info, 'allowable_children'):
            if source_info.module in dest_info.allowable_children:
                return 1
            if '*' in dest_info.allowable_children:
                return 1
        return 0

    def popup_handler (self, widget, event):
        if (event.type == GDK.BUTTON_PRESS):
            if (event.button == 3):
                (row, col) =  widget.get_selection_info (event.x, event.y)
                self.popup_node=widget.node_nth(row)
                self.popup_menu.popup (None, None, None, 
                                       event.button, event.time);
                return 1
        return 0

    def popup_delete_activated(self, widget, data=None):
        tree = self.editTree.get_widget ("instrumentTree")
        if self.oldSelection == self.popup_node:
            self.oldSelection = None
            table = self.editTree.get_widget("argumentTable")
            for c in table.children():
                table.remove(c)
        tree.remove_node(self.popup_node)

    def make_dom_tree(self, tree, treenode):
        (node, info) = tree.node_get_row_data(treenode)
        node.children = []
        for child in treenode.children:
            node.append(self.make_dom_tree(tree, child))
        return node
    
    def ok_clicked(self, widget, data=None):
        w = self.editTree.get_widget("editInstruments")
        tree = self.editTree.get_widget ("instrumentTree")
        self.update_attrs_from_window()
        delroot = save()
        delroot.tag = 'instruments-deleted'
        domroot = DOMNode('instruments')
        for treenode in tree.base_nodes():
            domroot.append(self.make_dom_tree(tree, treenode))
        domtree = DOMNode('show')
        domtree.append(domroot)
        deltree = DOMNode('show')
        deltree.append(delroot)
        for mod in lb.instrument_module_info.values():
            mod.load(deltree)
        for mod in lb.instrument_module_info.values():
            mod.load(domtree)            
        lb.sendData(delroot)        
        lb.sendData(domroot)
        w.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.editTree.get_widget("editInstruments")
        w.destroy()

    def remove_clicked(self, widget, data=None):
        self.popup_node = self.oldSelection
        self.popup_delete_activated(widget, data)
        
    def add_clicked(self, widget, data=None):
        tree = self.editTree.get_widget("instrumentTree")
        menu = self.editTree.get_widget("driverMenu")        
        name = menu.children()[0].get()
        info = lb.instrument_module_info[name]
        dnode = DOMNode (tag = info.module, attrs={'name': 'Unnamed'})
        if info.container:
            node = tree.insert_node(None, None, ['Unnamed'], is_leaf=FALSE)
        else:
            node = tree.insert_node(None, None, ['Unnamed'], is_leaf=TRUE)
        tree.node_set_row_data(node, (dnode, info))

    def add_group_clicked(self, widget, data=None):
        tree = self.editTree.get_widget("instrumentTree")
        info = group_info
        dnode = DOMNode (tag = 'group', attrs={'name': 'Unnamed'})
        node = tree.insert_node(None, None, ['Unnamed'], is_leaf=FALSE)
        tree.node_set_row_data(node, (dnode, info))

    def set_table (self, dict):
        l = len(dict)
        table = self.editTree.get_widget("argumentTable")
        for c in table.children():
            table.remove(c)
        table.resize(2,l)
        self.entryWidgets=[]
        x = 0
        for name, value in dict.items():
            label = GtkLabel(name)
            label.set_alignment(1.0, 0.5)
            label.show()
            table.attach(label, 0, 1, x, x+1, xoptions=FILL, yoptions=0)
            curval = value[0]
            value = value[1]

            if callable(value):
                value=value(dict)
            if type(value)==type([]):
                entry = GtkOptionMenu()
                menu=GtkMenu()
                menu.connect ("selection-done", self.update_and_redraw, None)
                count = 0
                current = 0
                for v in value:
                    if v == curval:
                        current = count
                    i=GtkMenuItem(v)
                    menu.append(i)
                    count = count +1
                menu.show_all()
                entry.set_menu(menu)
                entry.set_history(current)
            if type(value)==type(''):
                entry = GtkEntry()
                entry.set_text(curval)
            entry.show_all()
            align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
            align.add(entry)
            align.show()
            self.entryWidgets.append((name, entry))
            table.attach(align, 1, 2, x, x+1, xoptions=FILL, yoptions=0)
            x = x + 1

    def window_change(self, widget = None, data = None):
        tree = self.editTree.get_widget("instrumentTree")
        sel = tree.selection[0]
        lb.sel = sel
        data = tree.node_get_row_data(sel)
        dict = data[1].get_arguments(data[0])
        if sel.level > 1:
            parent_data = tree.node_get_row_data(sel.parent)
            dict.update(parent_data[1].get_arguments_for_children(data[0]))
        self.set_table (dict)

    def update_attrs_from_window(self, sel = None):
        tree = self.editTree.get_widget("instrumentTree")
        if (sel == None):
            try:
                sel = tree.selection[0]
            except:
                return
        data = tree.node_get_row_data(sel)

        attrs = {}
        for n,w in self.entryWidgets:
            new_value = ''
            if isinstance (w, GtkOptionMenu):
                new_value = w.children()[0].get()
            if isinstance (w, GtkEntry):            
                new_value = w.get_text()
            attrs[n]=new_value
        data[0].attrs = attrs

        tree.node_set_text(sel, 0, attrs['name'])


    def update_and_redraw(self, widget = None, data = None):
        self.update_attrs_from_window()
        self.window_change()

    def row_selected(self, widget, row, column, data=None):
        if self.oldSelection:
            self.update_attrs_from_window(self.oldSelection)

        tree = self.editTree.get_widget("instrumentTree")
        sel = tree.selection[0]
        self.oldSelection = sel

        self.window_change()

    def row_unselected(self, widget, row, column, data=None):
        if self.oldSelection:
            self.update_attrs_from_window(self.oldSelection)
        self.oldSelection = None
        table = self.editTree.get_widget("argumentTable")
        for c in table.children():
            table.remove(c)

    
