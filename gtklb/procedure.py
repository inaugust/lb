from threading import *
from os import path
import string, cStringIO
from ExpatXMLParser import DOMNode
import ExpatXMLParser
import gtk
from gtk import *
from gtk.glade import *

edit_menu = None

def initialize():
    reset()

def reset():
    global edit_menu
    lb.procedure={}
    gdk.threads_enter()
    menubar=lb.menubar
    for m in menubar.get_children():
        if (m.get_children()[0].get() == "Procedure"):
            menubar.remove(m)

    procedure1=gtk.MenuItem("Procedure")
    menubar.append(procedure1)

    procedure1_menu=gtk.Menu()
    procedure1.set_submenu(procedure1_menu)

    edit1=gtk.MenuItem("Edit")
    procedure1_menu.append(edit1)
    edit_menu=gtk.Menu()
    edit1.set_submenu(edit_menu)

    new1=gtk.MenuItem("New")
    new1.connect("activate", newProcedure_cb, None)
    procedure1_menu.append(new1)

    menubar.show_all()
    gdk.threads_leave()
    
def shutdown():
    pass

def load(tree):
    for section in tree.find("procedures"):
        for proc in section.find("procedure"):
            p = Procedure (proc.attrs['name'], proc.attrs['args'])
            p.set_proc (proc.data)

def save():
    tree = DOMNode('procedures')
    for i in lb.procedure.values():
        tree.append(i.to_tree())
    return tree

class procedureFactory:
    def ok_clicked(self, widget, data=None):
        win = self.newTree.get_widget("editProcedure")
        nameEntry = self.newTree.get_widget("nameEntry")
        argEntry = self.newTree.get_widget("argEntry")
        text = self.newTree.get_widget("text")
        name = nameEntry.get_text()
        args = argEntry.get_text()
        source = text.get_chars(0, text.get_length())
        if (string.strip(name) != ''):
            if not lb.procedure.has_key(name):
                gdk.threads_leave()
                p=Procedure(name, args)
                p.set_proc(source)
                p.send_update()
                gdk.threads_enter()
        win.destroy()

    def cancel_clicked(self, widget, data=None):
        win = self.newTree.get_widget("editProcedure")
        win.destroy()

    def __init__(self):
        gdk.threads_enter()
        try:
            wTree = glade.XML ("gtklb.glade",
                              "editProcedure")
            self.newTree = wTree
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
        finally:
            gdk.threads_leave()


def newProcedure_cb(widget, data=None):
    # called from menu
    gdk.threads_leave()
    f = procedureFactory()
    gdk.threads_enter()
    # that's it.
        
class Procedure:

    def __init__(self, name, args, update_refs=1):
        self.name = name
        self.set_args(args)
        self.proc = ''
        if (update_refs):
            self.update_refs()

    def update_refs(self):
        gdk.threads_enter()
        try:
            if (lb.procedure.has_key(self.name)):
                old = lb.procedure[self.name]
                edit_menu.remove(old.edit_menu_item)

            lb.procedure[self.name]=self

            i=gtk.MenuItem(self.name)
            self.edit_menu_item=i
            edit_menu.append(i)
            i.connect("activate", self.edit_cb, None)
            i.show()

        finally:
            gdk.threads_leave()

    def copy(self):
        p = Procedure(self.name, self.argstr, update_refs = 0)
        p.set_proc(self.proc)
        p.edit_menu_item = self.edit_menu_item
        return p
        
    def to_tree(self):
        args = ''
        for a in self.args:
            args=args+a+', '
        args=args[:-2]
        p = DOMNode('procedure', {'name':self.name, 'args':args})
        data = self.proc + "\n"
        p.add_data(data)
        return p

    def send_update(self):
        tree = DOMNode('procedures')
        tree.append(self.to_tree())
        lb.sendData(tree)

    def set_args (self, args):
        self.argstr = args
        if string.strip(args)=='':
            self.args=[]
        else:
            self.args = map(string.strip, string.split(args, ','))
        
    def set_proc (self, proc):
        sio=cStringIO.StringIO(proc)
        proc=''
        started = 0
        buffer = ''
        while (1):
            line=sio.readline()
            if not line: break
            if string.strip(line)=='':
                if started:
                    buffer=buffer+'\n'
            else:
                started = 1
                buffer=buffer+line
                proc = proc + buffer
                buffer = ''
        self.proc = proc
        self.comp=compile(proc, self.name,'exec')

    def argument_widget(self, args = None):
        l = len(self.args)
        table = gtk.Table(rows=l, cols=2)
        widget_list = []
        for x in range(0,l):
            name = self.args[x]
            label = gtk.Label(name)
            label.set_alignment(1.0, 0.5)
            label.show()
            table.attach(label, 0, 1, x, x+1, xoptions=FILL, yoptions=0)
            entry = gtk.Entry()
            if args and args.has_key(name):
                entry.set_text(args[name])
            entry.show_all()
            widget_list.append((name, entry))
            align = gtk.Alignment(0.0, 0.5, 0.0, 0.0)
            align.add(entry)
            align.show()
            table.attach(align, 1, 2, x, x+1, xoptions=FILL, yoptions=0)
        table.show_all()
        return (table, widget_list)

    def argument_dict_from_widget (self, widget_list):
        dict = {}
        for name, w in widget_list:
            dict[name]=w.get_text()
        return dict
            
    def edit_cb(self, widget, data):
        """ Called from lightboard->procedure->edit """
        self.edit_menu_item.set_sensitive(0)
        gdk.threads_leave()
        self.edit()
        gdk.threads_enter()


    def edit_ok_clicked(self, widget, data=None):
        win = self.editTree.get_widget("editProcedure")
        argEntry = self.editTree.get_widget("argEntry")
        text = self.editTree.get_widget("text")
        args = argEntry.get_text()
        source = text.get_chars(0, text.get_length())

        gdk.threads_leave()
        
        self.set_args(args)
        self.set_proc(source)
        self.update_refs()
        self.send_update()

        gdk.threads_enter()
        win.destroy()

    def edit_cancel_clicked(self, widget, data=None):
        win = self.editTree.get_widget("editProcedure")
        win.destroy()

    def edit_destroyed(self, widget, data=None):
        self.edit_menu_item.set_sensitive(1)

    def edit(self):
        p = self.copy()
        p.edit_self()
    
    def edit_self(self):
        gdk.threads_enter()
        try:
            wTree = glade.XML ("gtklb.glade",
                              "editProcedure")
            self.editTree = wTree
            
            dic = {"on_ok_clicked": self.edit_ok_clicked,
                   "on_cancel_clicked": self.edit_cancel_clicked}
            
            wTree.signal_autoconnect (dic)

            w = wTree.get_widget("editProcedure")
            w.connect ('destroy', self.edit_destroyed)

            w = wTree.get_widget("nameEntry")
            w.set_text(self.name)
            w.set_sensitive(0)

            w = wTree.get_widget("argEntry")
            w.set_text(self.argstr)
            w = wTree.get_widget("text")
            w.insert_defaults(self.proc)
            
        finally:
            gdk.threads_leave()



        
