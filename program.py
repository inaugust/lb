from threading import *
from xmllib import XMLParser
from os import path
import string
import process

def initialize(lb):
    lb.program={}
    try:
        f=open(path.join(lb.datapath, 'programs'))
    except:
        f=None
    if (f):
        p=parser()
        p.feed(f.read())
    lb.add_signal ('Program Run', program.run_real)
    lb.add_signal ('Program Stop', program.stop_real)
    lb.add_signal ('Program Step Forward', program.step_forward_real)
    lb.add_signal ('Program Set Next Step', program.set_next_step_real)
    lb.add_signal ('Program Step Start', None)
    lb.add_signal ('Program Step Halt', None)
    lb.add_signal ('Program Step Complete', None)
    
def shutdown():
    for p in lb.program.values():
        p.stop_real({})

class step:
    def __init__(self):
        self.name=''
        self.actions=[]

class loop:
    def __init__(self):
        self.name=''
        self.start=-1
        self.stop=-1
        self.actions=[]

class parser(XMLParser):

    def start_programs (self, attrs):
        pass
    
    def start_program (self, attrs):
        self.program=program (attrs['name'])
        self.pstack=[self.program]
        self.init=0

    def end_program (self):
        lb.program[self.program.name]=self.program

    def start_step (self, attrs):
        s = step ()
        self.pstack.append (s)
        if (attrs.has_key('name')):
            s.name=attrs['name']
        else:
            s.name="None"
            
    def end_step (self):
        s = self.pstack.pop ()
        top = self.pstack[-1]
        top.actions.append(s)

    def start_loop (self, attrs):
        print "loops not supported!"
        return
        l=loop()
        self.pstack.append (l)
        if (attrs.has_key('name')):
            l.name=attrs['name']
        l.start=int(attrs['start'])
        l.stop=int(attrs['stop'])
        if l.start<0 or l.stop<0:
            print "error"

    def end_loop (self):
        return
        l=self.pstack.pop()
        top = self.pstack[-1]
        top.actions.append(l)
        
    def start_init (self, attrs):
        s=step()
        self.pstack.append (s)
        if (attrs.has_key('name')):
            s.name=attrs['name']
        else:
            s.name='Init'
        self.init=self.init+1

    def end_init (self):
        self.init=self.init-1
        if (self.init==0):
            s=self.pstack.pop()
            self.program.init_step=s
        else:
            print "nested inits"
            
    def unknown_starttag (self, tag, attrs):
        tag=string.lower(tag)
        top=self.pstack[-1]
        top.actions.append ((tag, attrs))
        
class program:

    def __init__(self, name):
        self.name=name
        self.init_step=None
        self.actions=[]
        self.current_step=None
        self.next_step=None
        self.processes={}
        self.mythread=None
        self.threadlock=Lock()
        self.stepnumlock=Lock()

    def run (self):
        lb.send_signal ('Program Run', itself=self)

    def stop (self):
        lb.send_signal ('Program Stop', itself=self)

    def step_forward (self):
        lb.send_signal ('Program Step Forward', itself=self)

    def set_next_step (self, step):
        lb.send_signal ('Program Set Next Step', itself=self, step=step)

    def get_current_step (self):
        if (self.current_step != None):
            return self.actions[self.current_step]
        else:
            return None

    def get_next_step (self):
        if (self.next_step != None):
            return self.actions[self.next_step]
        else:
            return None
        
    #private
    
    def run_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.running=0
            self.steplock.release()
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        else:
            self.running=1
            self.steplock=Semaphore (0)
            self.current_step=None
            self.set_next_step(0)
            self.run_actions(self.init_step.actions)
            self.mythread=Thread (target=program.do_run, args=(self,
                                                               self.actions))
            self.mythread.start()
        self.threadlock.release()

    def stop_real (self, args):
        self.threadlock.acquire()
        if (self.mythread):
            self.running=0
            self.steplock.release()
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        
    def step_forward_real (self, args):
        self.steplock.release()

    def set_next_step_real (self, args):
        self.stepnumlock.acquire()
        self.next_step=args['step']
        self.stepnumlock.release()

    def do_run (self, actions):
        print 'do_run'
        self.run_steps ()
        self.threadlock.acquire()
        if (self.running):
            self.mythread=None
            # else, we were stopped, let stop handle it
        self.threadlock.release()

    def run_steps (self):        
        print 'run_steps'

        while (1):
            print 'step - waiting'
            self.steplock.acquire()
            print 'got it'
            if (not self.running): return
            self.stepnumlock.acquire()
            if (self.next_step >= len(self.actions)):
                self.stepnumlock.release()
                self.set_next_step(None)
                break
            self.current_step = self.next_step
            next = self.current_step + 1
            action=self.actions[self.current_step]
            self.stepnumlock.release()
            self.set_next_step(next)

            lb.send_signal ('Program Step Start', itself=self)
            self.run_actions (action.actions)
            lb.send_signal ('Program Step Complete', itself=self)

    def run_actions (self, actions):        
        print 'run_actions'

        for action in actions:
            print action
            print 'action - '+action[0]
            self.run_action (action[0], action[1])
        print 'run_actions done'
        
    def run_action (self, action, args):
        if (action=='levelfader_load'):
            if (args.has_key('cue')):
                lb.levelfader[args['levelfader']].set_cue(args['cue'])
            if (args.has_key('instrument')):
                lb.levelfader[args['levelfader']].set_instrument(args['instrument'])
        if (action=='levelfader_level'):
            lb.levelfader[args['levelfader']].set_level(args['level'])
        if (action=='levelfader_run'):
            time=args.get('time',0)
            lb.levelfader[args['levelfader']].run(args['level'], time)
        if (action=='xf_load'):
            u=lb.crossfader[args['xf']].get_up_faders()
            u[0].set_cue(args['cue'])
        if (action=='xf_run'):
            uptime=args.get('uptime', 0)
            downtime=args.get('downtime', 0)
            lb.crossfader[args['xf']].run(uptime, downtime)
        if (action=='proc_run'):
            p=process.process()
            self.processes[args['id']]=p
            p.start_with_args(lb.procedure[args['proc']], args)
        if (action=='proc_stop'):
            self.processes[args['id']].stop()
            del self.processes[args['id']]


