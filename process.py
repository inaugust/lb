from threading import *
from xmllib import XMLParser
from os import path
import string
import procedure

def initialize(lb):
    lb.process={}
    lb.process_lock=Lock()    
    lb.process_num=0
    lb.add_signal ('Process Start', process.start_real)
    lb.add_signal ('Process Stop', process.stop_real)
    
def shutdown():
    for p in lb.process.values():
        p.stop_real({})
        
class process:

    def __init__(self):
        self.mythread=None
        self.threadlock=Lock()
        self.name=None

    def get_name (self):
        return self.name

    def start (self, process_procedure, **args):
        lb.send_signal ('Process Start', itself=self,
                        process_procedure=process_procedure,
                        procargs=args)

    def start_with_args (self, process_procedure, args):
        lb.send_signal ('Process Start', itself=self,
                        process_procedure=process_procedure,
                        procargs=args)

    def stop (self):
        lb.send_signal ('Process Stop', itself=self)

    #private
    
    def start_real (self, args):
        if (self.name):
            print 'error'
            return
        lb.process_lock.acquire()
        name=lb.process_num
        self.name=name
        lb.process_num=lb.process_num+1
        lb.process[name]=self
        lb.process_lock.release()

        inproc=args['process_procedure']
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
                                    args['procargs']))
        self.mythread.start()
        self.threadlock.release()

    def stop_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.running=0
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()

    def do_run (self, process_procedure, args):
        print 'do_run'
        exec (process_procedure)
        self.threadlock.acquire()
        self.mythread=None
        self.threadlock.release()
        del lb.process[self.name]
