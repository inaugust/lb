from threading import *
from xmllib import XMLParser
from os import path
import string, cStringIO
import ExpatXMLParser
from gtk import *
from libglade import *

edit_menu = None

def initialize():
    reset()

def reset():
    global edit_menu
    lb.procedure={}
    threads_enter()
    menubar=lb.menubar
    for m in menubar.children():
        if (m.children()[0].get() == "Procedure"):
            menubar.remove(m)

    procedure1=GtkMenuItem("Procedure")
    menubar.append(procedure1)

    procedure1_menu=GtkMenu()
    procedure1.set_submenu(procedure1_menu)

    edit1=GtkMenuItem("Edit")
    procedure1_menu.append(edit1)
    edit_menu=GtkMenu()
    edit1.set_submenu(edit_menu)

    new1=GtkMenuItem("New")
    new1.connect("activate", newProcedure_cb, None)
    procedure1_menu.append(new1)

    menubar.show_all()
    threads_leave()
    
def shutdown():
    pass

def load(data):
    p=parser()
    p.Parse(data)
    p.close()

def save():
    s="<procedures>\n\n"
    for c in lb.procedure.values():
        s=s+c.to_xml(1)
    s=s+"</procedures>\n"
    return s


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
                threads_leave()
                p=procedure(name, args)
                p.set_proc(source)
                p.send_update()
                threads_enter()
        win.destroy()

    def cancel_clicked(self, widget, data=None):
        win = self.newTree.get_widget("editProcedure")
        win.destroy()

    def __init__(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "editProcedure")
            self.newTree = wTree
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
        finally:
            threads_leave()


def newProcedure_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = procedureFactory()
    threads_enter()
    # that's it.


class parser(ExpatXMLParser.ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.ExpatXMLParser.__init__(self)
        self.in_procedures=0
        self.proc = ''
        
    def start_procedures (self, attrs):
        self.in_procedures=1

    def end_procedures (self):
        self.in_procedures=0

    def start_procedure (self, attrs):
        if (not self.in_procedures): return
        self.procedure=procedure (attrs['name'], attrs['args'])
        self.proc = ''

    def end_procedure (self):
        if (not self.in_procedures): return
        self.procedure.set_proc (self.proc)
        self.procedure=None

    def handle_data (self, data):
        if (not self.in_procedures): return
        if (hasattr(self,'procedure') and self.procedure):
            self.proc=self.proc+data
        
class procedure:

    def __init__(self, name, args, update_refs=1):
        self.name = name
        self.set_args(args)
        self.proc = ''
        if (update_refs):
            self.update_refs()

    def update_refs(self):
        threads_enter()
        try:
            if (lb.procedure.has_key(self.name)):
                old = lb.procedure[self.name]
                edit_menu.remove(old.edit_menu_item)

            lb.procedure[self.name]=self

            i=GtkMenuItem(self.name)
            self.edit_menu_item=i
            edit_menu.append(i)
            i.connect("activate", self.edit_cb, None)
            i.show()

        finally:
            threads_leave()

    def copy(self):
        p = procedure(self.name, self.argstr, update_refs = 0)
        p.set_proc(self.proc)
        p.edit_menu_item = self.edit_menu_item
        return p
        
    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        args = ''
        for a in self.args:
            args=args+a+', '
        args=args[:-2]
        s = s + sp + '<procedure name="%s" args="%s">\n' % (self.name, args)
        s = s + ExpatXMLParser.reverse_translate_references(self.proc) + "\n"
        s = s + sp + '</procedure>\n'
        return s

    def send_update(self):
        s="<procedures>\n\n"
        s=s+self.to_xml(1)+"\n"
        s=s+"</procedures>\n"
        lb.sendData(s)

    def set_args (self, args):
        self.argstr = args
        if string.strip(args)=='':
            self.args=[]
        else:
            self.args = map(string.strip, string.split(args, ','))
        
    def set_proc (self, proc):
        self.proc = proc
        sio=cStringIO.StringIO(self.proc)
        proc=''
        while (1):
            line=sio.readline()
            if not line: break
            if string.strip(line)=='':
                proc=proc+'\n'
            else:
                proc=proc+line
        self.comp=compile(proc, self.name,'exec')

    def argument_widget(self, args = None):
        l = len(self.args)
        table = GtkTable(rows=l, cols=2)
        widget_list = []
        for x in range(0,l):
            name = self.args[x]
            label = GtkLabel(name)
            label.set_alignment(1.0, 0.5)
            label.show()
            table.attach(label, 0, 1, x, x+1, xoptions=FILL, yoptions=0)
            entry = GtkEntry()
            if args and args.has_key(name):
                entry.set_text(args[name])
            entry.show_all()
            widget_list.append((name, entry))
            align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
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
        threads_leave()
        self.edit()
        threads_enter()


    def edit_ok_clicked(self, widget, data=None):
        win = self.editTree.get_widget("editProcedure")
        argEntry = self.editTree.get_widget("argEntry")
        text = self.editTree.get_widget("text")
        args = argEntry.get_text()
        source = text.get_chars(0, text.get_length())

        threads_leave()
        
        self.set_args(args)
        self.set_proc(source)
        self.update_refs()
        self.send_update()

        threads_enter()
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
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
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
            threads_leave()



        
