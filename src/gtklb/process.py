from threading import *
from xmllib import XMLParser
from os import path
import string
import procedure

def initialize():
    reset()

def reset():
    lb.process={}
    lb.process_lock=Lock()    
    lb.process_num=0
    
def shutdown():
    for p in lb.process.values():
        p.stop_real({})
        
def load(data):
    pass

def save():
    pass

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
