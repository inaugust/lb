from threading import *
from xmllib import XMLParser
from os import path
import string
import procedure
from gtk import *
from libglade import *

start_menu = None
stop_menu = None

def initialize():
    reset()

def reset():
    global stop_menu
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

    new1=GtkMenuItem("New")
    new1.connect("activate", newProcess_cb, None)
    process1_menu.append(new1)

    menubar.show_all()
    threads_leave()
    
def shutdown():
    for p in lb.process.values():
        p.stop_real({})
        
def load(data):
    pass

def save():
    pass



class processFactory:
    def ok_clicked(self, widget, data=None):
        pass

    def cancel_clicked(self, widget, data=None):
        pass

    def procedure_changed(self, widget, data=None):
        menu = self.newTree.get_widget("procMenu")
        name = menu.children()[0].get()
        proc = lb.procedure[name]
        w = proc.argument_widget()
        frame = self.newTree.get_widget("frame")
        for c in frame.children():
            frame.remove(c)
        frame.add(w)

    def __init__(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "newProcess")
            self.newTree = wTree
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
            frame = wTree.get_widget("frame")
            entry = wTree.get_widget("procMenu")
            menu=GtkMenu()
            menu.connect ("selection-done", self.procedure_changed, None)
            print lb.procedure
            for proc in lb.procedure.keys():
                print proc
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







class process:

    def __init__(self):
        self.mythread=None
        self.threadlock=Lock()
        self.name=None

    def get_name (self):
        return self.name

    def start (self, process_procedure, **args):
        if (self.name):
            print 'error'
            return
        lb.process_lock.acquire()
        name=lb.process_num
        self.name=name
        lb.process_num=lb.process_num+1
        lb.process[name]=self
        lb.process_lock.release()

        inproc=process_procedure
        if (type(inproc)==type('string')):
            proc=lb.procedure[inproc]
        elif (isinstance (inproc, procedure.procedure)):
            proc=inproc.comp
        else: #callable
            proc=inproc
            
        self.threadlock.acquire()
        self.running=1
        self.mythread=Thread (target=process.do_run, 
                              args=(self, proc,
                                    args))
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

    # private

    def do_run (self, process_procedure, args):
        print 'do_run'
        exec (process_procedure)
        self.threadlock.acquire()
        self.mythread=None
        self.threadlock.release()
        del lb.process[self.name]

