from threading import *
from xmllib import XMLParser
from os import path
import string
import process
from ExpatXMLParser import ExpatXMLParser
from cue import cue
import time
from gtk import *
from libglade import *

run_menu=None

action_types={
    'xf_load': (('xf', lb.crossfader.keys), ('cue', lb.cue.keys)),
    'xf_run': (('xf', lb.crossfader.keys), ('uptime', ''),
               ('downtime', '')),
    }

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
    def __init__(self, my_prog):
        self.program = my_prog
        self.name=''
        self.actions=[]

    def window_change(self, widget=None, data=None):
        menu = self.editTree.get_widget("actionTypeMenu")
        name = menu.children()[0].get()
        args = action_types[name]
        l = len(args)
        table = self.editTree.get_widget("table")
        for c in table.children():
            table.remove(c)
        table.resize(3,l+1)
        for x in range (0, l):
            label = GtkLabel(args[x][0])
            label.show()
            table.attach(label, 0, 1, x, x+1)
            value = args[x][1]
            if callable(value):
                value=value()
            if type(value)==type([]):
                entry = GtkOptionMenu()
                menu=GtkMenu()
                entry.set_menu(menu)
                count = 0
                current = 0
                for v in value:
                    try:
                        if v == data[args[x][0]]:
                            current = count
                    except:
                        pass
                    i=GtkMenuItem(v)
                    menu.append(i)
                    count = count +1
                entry.set_history(current)
            if type(value)==type(''):
                entry = GtkEntry()
                current = ''
                try:
                    current = data[args[x][0]]
                except:
                    pass
                entry.set_text(current)
            entry.show_all()
            table.attach(entry, 1, 2, x, x+1)
            
    def edit_action(self, actnum):
        print 'edit', actnum
        (kind, args) = self.actions[actnum]
        wTree = GladeXML ("gtklb.glade",
                          "programActionEdit")
        table = wTree.get_widget("table")
        self.editTree = wTree
        
        optionMenu = self.editTree.get_widget("actionTypeMenu")
        
        menu=GtkMenu()
        menu.connect ("selection-done", self.window_change, None)
        optionMenu.set_menu(menu)
        count = 0
        current = 0
        for t in action_types.keys():
            if t == kind:
                current = count
            i=GtkMenuItem(t)
            i.show()
            menu.append(i)
            count = count +1
        optionMenu.set_history(current)
        menu.show()
        self.window_change(data = args)

    def name_ok_clicked(self, widget, data=None):
        win = self.nameTree.get_widget("programStepEdit")
        entry = self.nameTree.get_widget("entry")
        self.name = entry.get_text()
        self.program.update_tree()
        win.destroy()

    def name_cancel_clicked(self, widget, data=None):
        pass
    
    def edit_name(self):
        wTree = GladeXML ("gtklb.glade",
                          "programStepEdit")

        self.nameTree = wTree
        
        ok = self.nameTree.get_widget("ok")
        cancel = self.nameTree.get_widget("cancel")
        
        ok.connect ("clicked", self.name_ok_clicked, None)
        ok.connect ("clicked", self.name_cancel_clicked, None)

class loop(step):
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
        prog.show()
        threads_leave()
        self.program.create_window()

    def start_step (self, attrs):
        s = step (self.program)
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
        s=step(self.program)
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
            if (self.init_step is not None):
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
            xf = lb.fader[args['xf']]
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

    def edit_add_clicked(self, widget, data=None):
        l=self.editTree.get_widget("programTree").get_selection()
        (stepnum, actnum) = self.tree_dict[l[0]]
        if actnum == -1:
            self.actions.append(step(self))
            self.actions[len(self.actions)-1].edit_name()
        else:
            cstep = self.actions[stepnum]
            cstep.actions.append('', {})
            cstep.edit_action(len(cstep.actions)-1)
            
    def edit_remove_clicked(self, widget, data=None):
        pass

    def edit_edit_clicked(self, widget, data=None):
        l=self.editTree.get_widget("programTree").get_selection()
        (stepnum, actnum) = self.tree_dict[l[0]]
        if actnum == -1:
            self.actions[stepnum].edit_name()
        else:
            step = self.actions[stepnum]
            step.edit_action(actnum)

    def edit_selection_changed(self, widget, data=None):
        l=widget.get_selection()
        if len(l) == 0:
            b = self.editTree.get_widget("addAction")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("removeAction")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("editAction")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("addStep")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("removeStep")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("editStep")
            b.children()[0].set_sensitive(0)
        else:
            (stepnum, actnum) = self.tree_dict[l[0]]
            if actnum == -1:
                b = self.editTree.get_widget("addAction")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("removeAction")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("editAction")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("addStep")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("removeStep")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("editStep")
                b.children()[0].set_sensitive(1)
            else:
                b = self.editTree.get_widget("addAction")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("removeAction")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("editAction")
                b.children()[0].set_sensitive(1)
                b = self.editTree.get_widget("addStep")
                b.children()[0].set_sensitive(0)
                b = self.editTree.get_widget("removeStep")
                b.children()[0].set_sensitive(0)
                b = self.editTree.get_widget("editStep")
                b.children()[0].set_sensitive(0)
                    
    def update_tree(self):
        tree = self.editTree.get_widget ("programTree")
        for i in tree.children():
            tree.remove_item(i)
        self.tree_dict = {}
        item = GtkTreeItem("<init>")
        self.tree_dict[item]=[-1, -1]
        tree.append(item)
        subtree = GtkTree()
        item.set_subtree(subtree)
        subtree.show()
        act_count = 0
        if (self.init_step is not None):
            for act in self.init_step.actions:
                subitem = GtkTreeItem(act[0])
                self.tree_dict[subitem]=[-1, act_count]
                subtree.append(subitem)
                subitem.show()
                act_count = act_count + 1
        item.show()

        step_count = 0
        for step in self.actions:
            item = GtkTreeItem(step.name)
            self.tree_dict[item]=[step_count, -1]
            tree.append(item)
            subtree = GtkTree()
            item.set_subtree(subtree)
            subtree.show()
            act_count = 0
            for act in step.actions:
                subitem = GtkTreeItem(act[0])
                self.tree_dict[subitem]=[step_count, act_count]
                subtree.append(subitem)
                subitem.show()
                act_count = act_count + 1
            item.show()
            step_count = step_count + 1
        
    def edit(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "programEdit")
            dic = {"on_add_clicked": self.edit_add_clicked,
                   "on_remove_clicked": self.edit_remove_clicked,
                   "on_edit_clicked": self.edit_edit_clicked,
                   "on_programTree_selection_changed": self.edit_selection_changed}
            self.editTree=wTree
            wTree.signal_autoconnect (dic)
            
            self.update_tree()

        finally:
            threads_leave()
       
    def step_edit(self, stepnum):
        step = self.actions[stepnum]
        step.edit()

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
        
