from threading import *
from xmllib import XMLParser
from xml.parsers import expat
from ExpatXMLParser import ExpatXMLParser, DOMNode
from os import path
import string
import procedure
from gtk import *
from libglade import *
import traceback

start_menu = None
stop_menu = None
edit_menu = None


def action_process_start(args):
    proc = lb.process[args['process']]
    if not proc.running:
        proc.start()

def action_process_stop(args):
    proc = lb.process[args['process']]
    if proc.running:
        proc.stop()
    
def get_process_keys():
    l = lb.process.keys()
    l.sort()
    return l

def initialize():
    reset()
    lb.program_action_type['process_start'] = (
        action_process_start,
        (('process', get_process_keys),))
    lb.program_action_type['process_stop'] = (
        action_process_stop,
        (('process', get_process_keys),))

def reset():
    global start_menu
    global stop_menu
    global edit_menu
    lb.process={}
    lb.process_lock=Lock()    
    lb.process_num=0
    threads_enter()
    menubar=lb.menubar
    for m in menubar.children():
        if (m.children()[0].get() == "Process"):
            menubar.remove(m)

    process1=GtkMenuItem("Process")
    menubar.append(process1)

    process1_menu=GtkMenu()
    process1.set_submenu(process1_menu)

    start1=GtkMenuItem("Start")
    process1_menu.append(start1)
    start_menu=GtkMenu()
    start1.set_submenu(start_menu)

    stop1=GtkMenuItem("Stop")
    process1_menu.append(stop1)
    stop_menu=GtkMenu()
    stop1.set_submenu(stop_menu)

    edit1=GtkMenuItem("Edit")
    process1_menu.append(edit1)
    edit_menu=GtkMenu()
    edit1.set_submenu(edit_menu)

    new1=GtkMenuItem("New")
    new1.connect("activate", newProcess_cb, None)
    process1_menu.append(new1)

    menubar.show_all()
    threads_leave()
    
def shutdown():
    for p in lb.process.values():
        p.stop()
        
def load(tree):
    for section in tree.find("processes"):
        for proc in section.find("process"):
            name = procedure = None
            args = {}
            for k,v in proc.attrs.items():
                if k == 'name': name = v
                elif k == 'procedure': procedure = v
                else:
                    args[k]=v
            if (name is None or procedure is None):
                return
            p = Process(name, procedure, args)

def save():
    tree = DOMNode('processes')
    for i in lb.process.values():
        tree.append(i.to_tree())
    return tree

class processFactory:
    def ok_clicked(self, widget, data=None):
        win = self.newTree.get_widget("editProcess")
        menu = self.newTree.get_widget("procMenu")
        entry = self.newTree.get_widget("nameEntry")
        pname = menu.children()[0].get()
        proc = lb.procedure[pname]
        args = proc.argument_dict_from_widget (self.widget_list)
        name = entry.get_text()
        if (string.strip(name) != ''):
            if not lb.process.has_key(name):
                threads_leave()
                p=Process(name, pname, args)
                p.send_update()
                threads_enter()
        win.destroy()

    def cancel_clicked(self, widget, data=None):
        win = self.newTree.get_widget("editProcess")
        win.destroy()

    def procedure_changed(self, widget, data=None):
        menu = self.newTree.get_widget("procMenu")
        name = menu.children()[0].get()
        proc = lb.procedure[name]
        w, self.widget_list = proc.argument_widget()
        frame = self.newTree.get_widget("frame")
        for c in frame.children():
            frame.remove(c)
        frame.add(w)

    def __init__(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "editProcess")
            self.newTree = wTree
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
            frame = wTree.get_widget("frame")
            entry = wTree.get_widget("procMenu")
            menu=GtkMenu()
            menu.connect ("selection-done", self.procedure_changed, None)
            for proc in lb.procedure.keys():
                i=GtkMenuItem(proc)
                menu.append(i)
            entry.set_history(0)
            menu.show_all()
            entry.set_menu(menu)
            self.procedure_changed(menu)
        finally:
            threads_leave()


def newProcess_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = processFactory()
    threads_enter()
    # that's it.


class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_processes=0

    def start_processes (self, attrs):
        self.in_processes=1

    def end_processes (self):
        self.in_processes=0
        
    def start_process (self, attrs):
        if (not self.in_processes):
            return
        name = procedure = None
        args = {}
        for k,v in attrs.items():
            if k == 'name': name = v
            elif k == 'procedure': procedure = v
            else:
                args[k]=v
        if (name is None or procedure is None):
            return
        Process(name, procedure, args)

class Process:

    def __init__(self, name = None, procedure = None, args = None,
                 update_refs=1):
        self.mythread=None
        self.threadlock=Lock()
        self.name = name
        self.procedure = procedure
        self.args = args
        self.running = 0
        
        if (update_refs):
            self.update_refs()

    def update_refs(self):
        threads_enter()
        try:
            if (lb.process.has_key(self.name)):
                old = lb.process[self.name]
                threads_leave()
                old.stop()
                threads_enter()
                start_menu.remove(old.start_menu_item)
                stop_menu.remove(old.stop_menu_item)
                edit_menu.remove(old.edit_menu_item)

            lb.process[self.name]=self

            i=GtkMenuItem(self.name)
            self.start_menu_item=i
            start_menu.append(i)
            i.connect("activate", self.start_cb, None)
            i.show()
            i=GtkMenuItem(self.name)
            self.stop_menu_item=i
            stop_menu.append(i)
            i.connect("activate", self.stop_cb, None)
            i.set_sensitive(0)
            i.show()
            i=GtkMenuItem(self.name)
            self.edit_menu_item=i
            edit_menu.append(i)
            i.connect("activate", self.edit_cb, None)
            i.show()

        finally:
            threads_leave()

    def copy(self):
        p = Process(self.name, self.procedure, self.args, update_refs=0)
        p.start_menu_item = self.start_menu_item
        p.stop_menu_item = self.stop_menu_item
        p.edit_menu_item = self.edit_menu_item
        return p
        
    def get_name (self):
        return self.name

    def start (self):
        proc=lb.procedure[self.procedure].comp
            
        self.threadlock.acquire()
        self.started()
        self.running=1
        self.mythread=Thread (target=process.do_run, 
                              args=(self, proc,
                                    self.args))
        self.mythread.start()
        self.threadlock.release()

    def stop (self):
        self.threadlock.acquire()
        if (self.mythread):
            self.running=0
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()

    def to_tree(self):
        dict = self.args.copy()
        dict['name'] = self.name
        dict['procedure'] = self.procedure
        p = DOMNode('process', dict)
        return p

    def send_update(self):
        tree = DOMNode('processes')
        tree.append(self.to_tree())
        lb.sendData(tree)

    # private

    def do_run (self, process_procedure, args):
        try:
            exec (process_procedure)
        except:
            traceback.print_exc()
        self.threadlock.acquire()
        self.mythread=None
        self.stopped()
        self.threadlock.release()


    def started(self):
        threads_enter()
        self.start_menu_item.set_sensitive(0)
        self.stop_menu_item.set_sensitive(1)
        self.edit_menu_item.set_sensitive(0)
        threads_leave()
        
    def stopped(self):
        threads_enter()
        self.start_menu_item.set_sensitive(1)
        self.stop_menu_item.set_sensitive(0)
        self.edit_menu_item.set_sensitive(1)
        threads_leave()
        
    def start_cb(self, widget, data=None):
        """ Called from lightboard->process->start """
        threads_leave()
        self.start()
        threads_enter()

    def stop_cb(self, widget, data=None):
        """ Called from lightboard->process->stop """
        threads_leave()
        self.stop()
        threads_enter()

    def edit(self):
        p = self.copy()
        p.edit_self()

    def edit_cb(self, widget, data):
        """ Called from lightboard->process->edit """
        self.edit_menu_item.set_sensitive(0)
        threads_leave()
        self.edit()
        threads_enter()


    def edit_ok_clicked(self, widget, data=None):
        win = self.editTree.get_widget("editProcess")
        menu = self.editTree.get_widget("procMenu")
        pname = menu.children()[0].get()
        proc = lb.procedure[pname]
        args = proc.argument_dict_from_widget (self.widget_list)

        threads_leave()
        self.procedure = pname
        self.args = args
        self.update_refs()
        self.send_update()
        threads_enter()
        
        win.destroy()

    def edit_cancel_clicked(self, widget, data=None):
        win = self.editTree.get_widget("editProcess")
        win.destroy()

    def edit_destroyed(self, widget, data=None):
        self.edit_menu_item.set_sensitive(1)

    def procedure_changed(self, widget, data=None):
        menu = self.editTree.get_widget("procMenu")
        name = menu.children()[0].get()
        proc = lb.procedure[name]
        args = None
        if name == self.procedure:
            args = self.args
        w, self.widget_list = proc.argument_widget(args)
        frame = self.editTree.get_widget("frame")
        for c in frame.children():
            frame.remove(c)
        frame.add(w)

    def edit_self(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "editProcess")
            self.editTree = wTree
            
            dic = {"on_ok_clicked": self.edit_ok_clicked,
                   "on_cancel_clicked": self.edit_cancel_clicked}

            wTree.signal_autoconnect (dic)

            w = wTree.get_widget("editProcess")
            w.connect ('destroy', self.edit_destroyed)

            w = wTree.get_widget("nameEntry")
            w.set_text(self.name)
            w.set_sensitive(0)
            
            frame = wTree.get_widget("frame")
            entry = wTree.get_widget("procMenu")
            menu=GtkMenu()
            menu.connect ("selection-done", self.procedure_changed, None)
            count = 0
            current = 0
            for proc in lb.procedure.keys():
                if proc == self.procedure:
                    current = count
                i=GtkMenuItem(proc)
                menu.append(i)
                count = count+1
            entry.set_history(current)
            menu.show_all()
            entry.set_menu(menu)
            self.procedure_changed(menu)
        finally:
            threads_leave()

