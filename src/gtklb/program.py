from threading import *
from xmllib import XMLParser
from os import path
import string
import process
from ExpatXMLParser import ExpatXMLParser
from cue import cue
import time
from gtk import *

run_menu=None

def initialize(lb):
    global run_menu
    lb.program={}

    threads_enter()
    menubar=lb.menubar
    program1=GtkMenuItem("Program")
    menubar.append(program1)

    program1_menu=GtkMenu()
    program1.set_submenu(program1_menu)

    run1=GtkMenuItem("Run")
    program1_menu.append(run1)
    run_menu=GtkMenu()
    run1.set_submenu(run_menu)

    menubar.show_all()
    threads_leave()

    try:
        f=open(path.join(lb.datapath, 'programs'))
    except:
        f=None
    if (f):
        p=parser()
        p.Parse(f.read())
        p.close()
    
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

class parser(ExpatXMLParser):

    def start_programs (self, attrs):
        pass
    
    def start_program (self, attrs):
        self.program=program (attrs['name'])
        self.pstack=[self.program]
        self.init=0

    def end_program (self):
        lb.program[self.program.name]=self.program

        threads_enter()
        prog=GtkMenuItem(self.program.name)
        self.program.run_menu_item=prog
        run_menu.append(prog)
        prog.connect("activate", self.program.run_cb, None)
        #prog1.GTKPY_MAIN = window1Widget
        prog.show()
        threads_leave()
        self.program.create_window()

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
        
    def run (self):
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

    def stop (self):
        self.threadlock.acquire()
        if (self.mythread):
            self.running=0
            self.steplock.release()
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
        self.threadlock.release()
        
    def step_forward (self):
        self.steplock.release()

    def set_next_step (self, step):
        self.stepnumlock.acquire()
        self.next_step=step
        self.ui_set_next_step()
        self.stepnumlock.release()

    # private


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

            #lb.send_signal ('Program Step Start', itself=self)
            self.ui_step_start()
            self.run_actions (action.actions)
            self.ui_step_complete()
            #lb.send_signal ('Program Step Complete', itself=self)

    def run_actions (self, actions):        
        print 'run_actions'

        for action in actions:
            print action
            print 'action - '+action[0]
            self.run_action (action[0], action[1])
        print 'run_actions done'
        
    def run_action (self, action, args):
        ### Level fader
        if (action=='levelfader_load'):
            if (args.has_key('cue')):
                lb.levelfader[args['levelfader']].set_cue(args['cue'])
            if (args.has_key('instrument')):
                lb.levelfader[args['levelfader']].set_instrument(args['instrument'])
        if (action=='levelfader_level'):
            lb.levelfader[args['levelfader']].set_level(args['level'])
        if (action=='levelfader_run'):
            intime=args.get('time',0)
            lb.levelfader[args['levelfader']].run(args['level'], intime)

        ### Transition fader

        if (action=='transitionfader_set_start'):
            lb.transitionfader[args['transitionfader']].set_start_cue(args['cue'])
        if (action=='transitionfader_set_end'):
            lb.transitionfader[args['transitionfader']].set_end_cue(args['cue'])
        if (action=='transitionfader_set_attributes'):
            attrs=map(string.strip, string.split(args['attributes'], ','))
            lb.transitionfader[args['transitionfader']].set_attributes(attrs)
        if (action=='transitionfader_level'):
            lb.transitionfader[args['transitionfader']].set_level(args['level'])
        if (action=='transitionfader_run'):
            intime=args.get('time',0)
            lb.transitionfader[args['transitionfader']].run(args['level'], intime)
        ### Cross fader

        if (action=='xf_load'):
            import time
            print time
            start = time.time()
            xf = lb.crossfader[args['xf']]
            print 1
            old_cue = xf.getUpCueName()
            print 'old_cue', old_cue
            if (old_cue):
                print 'found'
                cue1=lb.cue[old_cue]
            else:
                print 'blank'
                cue1=cue("")
            cue2=lb.cue[args['cue']]
            print 2            
            #(cue1,cue2)=cue1.normalize(cue2)
            print cue1.core_cue, cue2.core_cue
            print cue1.name, cue2.name
            #print cue1.ins
            xf.setCues (cue1, cue2)
            end = time.time()
            print 'loaded in ', end-start
            
        if (action=='xf_run'):
            import time
            start = time.time()
            xf = lb.crossfader[args['xf']]
            
            uptime=lb.time_to_seconds(args.get('uptime', 0))
            downtime=lb.time_to_seconds(args.get('downtime', 0))
            xf.setTimes(uptime, downtime)

            if (downtime>uptime): intime=downtime
            else: intime=uptime
            intime=args.get('time', intime)
            end = time.time()
            print 'prep to run in ', end-start
            xf.run(100.0, intime)

        ### Procedure
            
        if (action=='proc_run'):
            p=process.process()
            self.processes[args['id']]=p
            p.start_with_args(lb.procedure[args['proc']], args)
        if (action=='proc_stop'):
            self.processes[args['id']].stop()
            del self.processes[args['id']]

    # UI methods

    def create_window(self):
        threads_enter()
        window1=GtkWindow(WINDOW_TOPLEVEL)
        self.window=window1
        window1.set_title(self.name)
        window1.set_default_size(300, 200)
        window1.set_policy(FALSE, TRUE, FALSE)
        window1.set_position(WIN_POS_NONE)
        
        vbox1=GtkVBox()
        window1.add(vbox1)
        vbox1.set_homogeneous(FALSE)
        vbox1.set_spacing(0)
        
        hbox1=GtkHBox()
        vbox1.pack_start(hbox1, FALSE, FALSE, 0)
        hbox1.set_homogeneous(TRUE)
        hbox1.set_spacing(0)
        
        self.label_cur=GtkLabel("Current: ---")
        self.label_next=GtkLabel("Next: ---")
        
        hbox1.pack_start(self.label_cur, FALSE, FALSE, 0)
        hbox1.pack_start(self.label_next, FALSE, FALSE, 0)

        scrolledwindow1=GtkScrolledWindow()
        vbox1.pack_start(scrolledwindow1, TRUE, TRUE, 0)
        scrolledwindow1.set_usize(-1, 200)
        #scrolledwindow1.set_policy(POLICY_ALWAYS, POLICY_ALWAYS)

        self.cue_list=GtkList()
        scrolledwindow1.add_with_viewport(self.cue_list)

        items=[]
        print self.actions
        for i in self.actions:
            print i, i.name
            item=GtkListItem(i.name)
            items.append(item)
        self.cue_list.append_items(items)

        self.cue_list_handler_id=self.cue_list.connect('selection_changed', self.selection_changed, None)

        hbuttonbox1=GtkHButtonBox()
        vbox1.pack_start(hbuttonbox1, TRUE, TRUE, 0)
        self.button_stop=GtkButton("Stop")
        hbuttonbox1.pack_start(self.button_stop, TRUE, TRUE, 0)
        self.button_stop.connect('clicked', self.stop_clicked, None)

        self.button_go=GtkButton("Go")
        hbuttonbox1.pack_start(self.button_go, TRUE, TRUE, 0)
        self.button_go.connect('clicked', self.go_clicked, None)

        threads_leave()

    def ui_step_start(self):
        threads_enter()
        self.button_go.set_sensitive(0)
    
        print 'startevt', self.get_current_step()
        if (self.get_current_step()):
            self.label_cur.set_text('Current: '+self.get_current_step().name)
        threads_leave()

    def ui_step_complete(self):
        threads_enter()
        self.button_go.set_sensitive(1)
        threads_leave()

    def ui_set_next_step(self):
        if (self.get_next_step()):
            threads_enter()
            #self.cue_list.disconnect(self.cue_list_handler_id)

            self.label_next.set_text('Next: '+self.get_next_step().name)
            self.cue_list.unselect_all()
            self.cue_list.select_item(self.next_step)

            #self.cue_list_handler_id=self.cue_list.connect('selection_changed', self.selection_changed, None)

            threads_leave()

    def stop_clicked(self, widget, data):
        pass

    def go_clicked(self, widget, data):
        self.step_forward()

    def selection_changed(self, widget, data):
        print 'changed'
        print widget.get_selection()
        sel=widget.get_selection()
        if (not sel):
            return
        p=widget.child_position(sel[0])
        print p
        if (p==self.next_step):
            return
        threads_leave()
        self.set_next_step(p)
        threads_enter()

    def run_cb(self, widget, data):
        """ Called from lightboard->program->run """

        self.run_menu_item.set_sensitive(0)
        self.window.show_all()

        threads_leave()
        self.run()
        threads_enter()
        
