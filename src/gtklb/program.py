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
edit_menu=None

action_types={
    'crossfader_load': (('crossfader', lb.crossfader.keys),
                        ('cue', lb.cue.keys)),
    'crossfader_run': (('crossfader', lb.crossfader.keys), ('uptime', ''),
                       ('downtime', '')),
    
    'levelfader_load': (('levelfader', lb.levelfader.keys),
                        ('cue', lb.cue.keys)),
    'levelfader_run': (('levelfader', lb.levelfader.keys), ('time', '')),
    }

def format_step(name, arg_dict):
    k = arg_dict.keys()
    k.sort()
    str=name
    for arg in k:
        str=str+"  "+arg + " = " + arg_dict[arg]
    return str

def initialize():
    reset()

def reset():
    global run_menu
    global edit_menu
    lb.program={}
    threads_enter()
    menubar=lb.menubar
    for m in menubar.children():
        if (m.children()[0].get() == "Program"):
            menubar.remove(m)

    program1=GtkMenuItem("Program")
    menubar.append(program1)

    program1_menu=GtkMenu()
    program1.set_submenu(program1_menu)

    run1=GtkMenuItem("Run")
    program1_menu.append(run1)
    run_menu=GtkMenu()
    run1.set_submenu(run_menu)

    edit1=GtkMenuItem("Edit")
    program1_menu.append(edit1)
    edit_menu=GtkMenu()
    edit1.set_submenu(edit_menu)

    new1=GtkMenuItem("New")
    new1.connect("activate", newProgram_cb, None)
    program1_menu.append(new1)

    menubar.show_all()
    threads_leave()
    
def shutdown():
    for p in lb.program.values():
        p.stop()

def load(data):
    p=parser()
    p.Parse(data)
    p.close()

def save():
    s="<programs>\n\n"
    for p in lb.program.values():
        s=s+p.to_xml(1)+"\n"
    s=s+"</programs>\n"
    return s

class programFactory:
    def __init__(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "nameDialog")
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked}
            
            wTree.signal_autoconnect (dic)
            
            self.tree=wTree
        finally:
            threads_leave()
        
    def ok_clicked(self, widget, data=None):
        w = self.tree.get_widget("nameDialog")
        e = self.tree.get_widget("nameEntry")
        name = e.get_text()
        if not lb.program.has_key(name):
            threads_leave()
            p=program(name)
            threads_enter()
        w.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.tree.get_widget("nameDialog")
        w.destroy()


def newProgram_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = programFactory()
    threads_enter()
    # that's it.

class action:
    def __init__(self, my_prog):
        self.program = my_prog
        self.kind = 'no-op'
        self.args = {}

    def copy(self):
        s = action(self.program)
        s.kind = self.kind
        s.args = self.args.copy()
        return s
    
    def window_change(self, widget=None, data=None):
        menu = self.editTree.get_widget("actionTypeMenu")
        name = menu.children()[0].get()
        args = action_types[name]
        l = len(args)
        table = self.editTree.get_widget("table")
        for c in table.children():
            table.remove(c)
        table.resize(2,l)
        self.entryWidgets=[]
        for x in range (0, l):
            label = GtkLabel(args[x][0])
            label.set_alignment(1.0, 0.5)
            label.show()
            table.attach(label, 0, 1, x, x+1, xoptions=FILL, yoptions=0)
            value = args[x][1]
            if callable(value):
                value=value()
            if type(value)==type([]):
                entry = GtkOptionMenu()
                menu=GtkMenu()
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
                menu.show_all()
                entry.set_menu(menu)
            if type(value)==type(''):
                entry = GtkEntry()
                current = ''
                try:
                    current = data[args[x][0]]
                except:
                    pass
                entry.set_text(current)
            entry.show_all()
            align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
            align.add(entry)
            align.show()
            self.entryWidgets.append(entry)
            table.attach(align, 1, 2, x, x+1, xoptions=FILL, yoptions=0)

    def ok_clicked(self, widget, data=None):
        menu = self.editTree.get_widget("actionTypeMenu")
        win = self.editTree.get_widget("programActionEdit")
        name = menu.children()[0].get()
        args = action_types[name]
        l = len(args)

        self.kind=name
        self.args={}
        
        for x in range (0, l):
            value = args[x][1]
            newvalue = ''
            if callable(value):
                value=value()
            if type(value)==type([]):
                new_value = self.entryWidgets[x].children()[0].get()
            if type(value)==type(''):
                new_value = self.entryWidgets[x].get_text()
            self.args[args[x][0]]=new_value
            self.program.update_tree(nodeData=self)
        win.destroy()
            
    def edit(self):
        wTree = GladeXML ("gtklb.glade",
                          "programActionEdit")
        table = wTree.get_widget("table")
        self.editTree = wTree
        
        optionMenu = self.editTree.get_widget("actionTypeMenu")
        win = self.editTree.get_widget("programActionEdit")
        ok = self.editTree.get_widget("ok")
        ok.connect("clicked", self.ok_clicked)
        cancel = self.editTree.get_widget("cancel")
        cancel.connect("clicked", win.destroy)
        
        menu=GtkMenu()
        menu.connect ("selection-done", self.window_change, None)
        count = 0
        current = 0
        for t in action_types.keys():
            if t == self.kind:
                current = count
            i=GtkMenuItem(t)
            i.show()
            menu.append(i)
            count = count +1
        menu.show_all()
        optionMenu.set_menu(menu)
        optionMenu.set_history(current)
        menu.show()
        self.window_change(data = self.args)


class step:
    def __init__(self, my_prog):
        self.program = my_prog
        self.name=''
        self.actions=[]

    def copy(self):
        s = step(self.program)
        s.name = self.name
        s.actions = map(lambda(x): x.copy(), self.actions)
        return s

    def ok_clicked(self, widget, data=None):
        win = self.nameTree.get_widget("programStepEdit")
        entry = self.nameTree.get_widget("entry")
        self.name = entry.get_text()
        self.program.update_tree(nodeData=self)
        win.destroy()

    def edit(self):
        wTree = GladeXML ("gtklb.glade",
                          "programStepEdit")

        self.nameTree = wTree
        
        ok = self.nameTree.get_widget("ok")
        cancel = self.nameTree.get_widget("cancel")
        win = self.nameTree.get_widget("programStepEdit")
        
        ok.connect ("clicked", self.ok_clicked, None)
        cancel.connect ("clicked", win.destroy)

class loop(step):
    def __init__(self):
        self.name=''
        self.start=-1
        self.stop=-1
        self.actions=[]

class parser(ExpatXMLParser):
    def __init__(self):
        ExpatXMLParser.__init__(self)
        self.in_programs=0
        
    def start_programs (self, attrs):
        self.in_programs=1

    def end_programs (self):
        self.in_programs=0
    
    def start_program (self, attrs):
        if (not self.in_programs): return
        self.program=program (attrs['name'])
        self.pstack=[self.program]
        self.init=0

    def end_program (self):
        if (not self.in_programs): return
        pass
    
    def start_step (self, attrs):
        if (not self.in_programs): return
        s = step (self.program)
        self.pstack.append (s)
        if (attrs.has_key('name')):
            s.name=attrs['name']
        else:
            s.name="None"
            
    def end_step (self):
        if (not self.in_programs): return
        s = self.pstack.pop ()
        top = self.pstack[-1]
        top.actions.append(s)

    def start_loop (self, attrs):
        if (not self.in_programs): return
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
        if (not self.in_programs): return
        return
        l=self.pstack.pop()
        top = self.pstack[-1]
        top.actions.append(l)
        
    def start_init (self, attrs):
        if (not self.in_programs): return
        s=step(self.program)
        self.pstack.append (s)
        s.name='<init>'
        self.init=self.init+1

    def end_init (self):
        if (not self.in_programs): return
        self.init=self.init-1
        if (self.init==0):
            s=self.pstack.pop()
            self.program.init_step=s
        else:
            print "nested inits"
            
    def unknown_starttag (self, tag, attrs):
        if (not self.in_programs): return
        tag=string.lower(tag)
        top=self.pstack[-1]
        act = action(self.program)
        act.kind = tag
        act.args = attrs
        top.actions.append (act)
        

class program:

    def __init__(self, name):
        self.name=name
        self.init_step=step(self)
        self.init_step.name='<init>'
        self.actions=[]
        self.current_step=None
        self.next_step=None
        self.processes={}
        self.mythread=None
        self.threadlock=Lock()
        self.stepnumlock=Lock()

        if (lb.program.has_key(self.name)):
            old = lb.program[self.name]
            run_menu.remove(old.run_menu_item)
            edit_menu.remove(old.edit_menu_item)
        lb.program[self.name]=self

        threads_enter()
        try:
            prog=GtkMenuItem(self.name)
            self.run_menu_item=prog
            run_menu.append(prog)
            prog.connect("activate", self.run_cb, None)
            prog.show()
            prog=GtkMenuItem(self.name)
            self.edit_menu_item=prog
            edit_menu.append(prog)
            prog.connect("activate", self.edit_cb, None)
            prog.show()
        finally:
            threads_leave()

    def get_current_step (self):
        if (self.current_step != None):
            return self.actions[self.current_step]
        else:
            return None

    def get_next_step (self):
        if (self.next_step != None and self.next_step <len(self.actions)):
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

    def to_xml(self, indent=0):
        s = ''
        sp = '  '*indent
        s=s+sp+'<program name="%s">\n' % self.name
        s=s+sp+'  <init>\n'
        for act in self.init_step.actions:
            l='    <%s' % act.kind
            for a,v in act.args.items():
                l=l+' %s="%s"' % (a,v)
            l=l+'/>\n'
            s=s+sp+l
        s=s+sp+'  </init>\n'
        for stp in self.actions:
            s=s+sp+'  <step name="%s">\n' % stp.name
            for act in stp.actions:
                l='    <%s' % act.kind
                for a,v in act.args.items():
                    l=l+' %s="%s"' % (a,v)
                l=l+'/>\n'
                s=s+sp+l
            s=s+sp+'  </step>\n'
        s=s+sp+'</program>\n'
        return s

    # private

    def do_run (self, actions):
        self.run_steps ()
        self.threadlock.acquire()
        if (self.running):
            self.mythread=None
            # else, we were stopped, let stop handle it
        self.threadlock.release()

    def run_steps (self):        
        while (1):
            self.steplock.acquire()
            if (not self.running): return
            self.stepnumlock.acquire()
            if (self.next_step >= len(self.actions)):
                self.stepnumlock.release()
                self.set_next_step(None)
                continue
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
        for action in actions:
            self.run_action (action.kind, action.args)
        
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

        if (action=='crossfader_load'):
            xf = lb.crossfader[args['crossfader']]
            old_cue = xf.getUpCueName()
            if (old_cue and lb.cue.has_key(old_cue)):
                cue1=lb.cue[old_cue]
            else:
                old_cue = xf.getDownCueName()
                if (old_cue and lb.cue.has_key(old_cue)):
                    cue1=lb.cue[old_cue]
                else:
                    cue1=cue("")
            cue2=lb.cue[args['cue']]
            xf.setCues (cue1, cue2)
            xf.setLevel(0.0)
            
        if (action=='crossfader_run'):
            xf = lb.crossfader[args['crossfader']]
            
            uptime=lb.value_to_core('time', args.get('uptime', 0))
            downtime=lb.value_to_core('time', args.get('downtime', 0))
            xf.setTimes(uptime, downtime)

            if (downtime>uptime): intime=downtime
            else: intime=uptime
            intime=args.get('time', intime)
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

    def edit_add_step_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        s = step(self)
        s.name = "<unnamed>"
        node = tree.insert_node(None, current.sibling, [s.name],
                                is_leaf=FALSE)
        tree.node_set_row_data(node, s)
        s.edit()

    def edit_add_action_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        act = action(self)
        if (current.level == 1):
            parent = current
            sibling = None
        else:
            parent = current.parent
            sibling = current.sibling
        node = tree.insert_node(parent, sibling, [act.kind],
                                is_leaf=TRUE)
        tree.node_set_row_data(node, act)
        act.edit()
            
    def edit_remove_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        tree.remove_node(current)

    def edit_edit_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        n = tree.node_get_row_data(current)
        n.edit()

    def edit_row_unselected(self, widget, row, column, data=None):
        l=self.editTree.get_widget("programTree").selection
        if len(l) == 0:
            b = self.editTree.get_widget("addStep")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("addAction")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("remove")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("edit")
            b.children()[0].set_sensitive(0)

    def edit_row_selected(self, widget, row, column, data=None):
        l=self.editTree.get_widget("programTree").selection
        if l[0].level==1:
            b = self.editTree.get_widget("addAction")
            b.children()[0].set_sensitive(1)
            b = self.editTree.get_widget("addStep")
            b.children()[0].set_sensitive(1)
            b = self.editTree.get_widget("remove")
            b.children()[0].set_sensitive(1)
            b = self.editTree.get_widget("edit")
            b.children()[0].set_sensitive(1)
        else:
            b = self.editTree.get_widget("addAction")
            b.children()[0].set_sensitive(1)
            b = self.editTree.get_widget("addStep")
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("remove")
            b.children()[0].set_sensitive(1)
            b = self.editTree.get_widget("edit")
            b.children()[0].set_sensitive(1)
                
    def update_tree(self, nodeData=None):
        tree = self.editTree.get_widget ("programTree")
        if (nodeData is not None):
            node = tree.find_by_row_data(None, nodeData)
            if (node.level==1):
                str = format_step (nodeData.name, {})
            if (node.level==2):
                str = format_step (nodeData.kind, nodeData.args)
            tree.node_set_text(node, 0, str)
            return
        tree.set_reorderable(1)

        istep = self.init_step.copy()

        str = format_step (istep.name, {})
        stepNode=tree.insert_node(None, None, [str], is_leaf=FALSE)
        tree.node_set_row_data(stepNode, istep)
        for act in istep.actions:
            str = format_step (act.kind, act.args)
            n=tree.insert_node(StepNode, None, [str], is_leaf=TRUE)
            tree.node_set_row_data(n, act)

        for step in self.actions:
            #should be self.steps
            step = step.copy()
            str = format_step (step.name, {})
            stepNode=tree.insert_node(None, None, [str], is_leaf=FALSE)
            tree.node_set_row_data(stepNode, step)
            
            for act in step.actions:
                str = format_step (act.kind, act.args)
                n=tree.insert_node(stepNode, None, [str], is_leaf=TRUE)
                tree.node_set_row_data(n, act)

    def edit_ok_clicked(self, widget, data=None):
        win = self.editTree.get_widget ("programEdit")
        tree = self.editTree.get_widget ("programTree")
        self.actions = []
        self.init_step = step(self)
        self.init_step.name = '<init>'
        for node in tree.base_nodes():
            s = tree.node_get_row_data(node)
            if (s.name == '<init>'):
                self.init_step = s
            else:
                self.actions.append(s)
            s.actions = []
            for child in node.children:
                a = tree.node_get_row_data(child)
                s.actions.append(a)
        win.destroy()
        
    def edit_cancel_clicked(self, widget, data=None):
        win = self.editTree.get_widget ("programEdit")
        win.destroy()

    def edit_drag_compare(self, source, parent, sibling):
        if (source.level==1 and parent):
            return 0
        if (source.level==2 and parent is None):
            return 0
        return 1

    def edit_destroyed(self, widget, data=None):
        self.edit_menu_item.set_sensitive(1)        
    
    def edit(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "programEdit")

            w = wTree.get_widget("programEdit")
            w.connect ('destroy', self.edit_destroyed)
            w = wTree.get_widget("programTree")
            w.connect ('select_row', self.edit_row_selected)
            w.connect ('unselect_row', self.edit_row_unselected)
            w.set_drag_compare_func(self.edit_drag_compare)

            self.editTree=wTree

            b = self.editTree.get_widget("addAction")
            b.connect("clicked", self.edit_add_action_clicked)
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("addStep")
            b.connect("clicked", self.edit_add_step_clicked)
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("remove")
            b.connect("clicked", self.edit_remove_clicked)
            b.children()[0].set_sensitive(0)
            b = self.editTree.get_widget("edit")
            b.connect("clicked", self.edit_edit_clicked)
            b.children()[0].set_sensitive(0)

            b = self.editTree.get_widget("ok")
            b.connect("clicked", self.edit_ok_clicked)
            b = self.editTree.get_widget("cancel")
            b.connect("clicked", self.edit_cancel_clicked)
            
            self.update_tree()

        finally:
            threads_leave()

    def edit_cb(self, widget, data):
        """ Called from lightboard->program->edit """

        self.edit_menu_item.set_sensitive(0)
        threads_leave()
        self.edit()
        threads_enter()
       
    def create_window(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "programRun")
            
            dic = {"on_go_clicked": self.go_clicked,
                   "on_stop_clicked": self.stop_clicked,
                   "on_list_selection_changed": self.selection_changed}
            
            wTree.signal_autoconnect (dic)
            
            w=wTree.get_widget ("programRun")
            self.window = w
            w.set_title("Program %s" % self.name)
            w.connect ('destroy', self.run_destroyed)

            self.label_cur=wTree.get_widget("currentLabel")
            self.label_next=wTree.get_widget("nextLabel")

            self.button_stop=wTree.get_widget("stop")
            self.button_go=wTree.get_widget("go")
        
            self.cue_list=wTree.get_widget("list")

            items=[]
            for i in self.actions:
                item=GtkListItem(i.name)
                item.show()
                items.append(item)
            self.cue_list.append_items(items)
        finally:
            threads_leave()

    def ui_step_start(self):
        threads_enter()
        self.button_go.set_sensitive(0)
    
        if (self.get_current_step()):
            self.label_cur.set_text('Current: '+self.get_current_step().name)
        threads_leave()

    def ui_step_complete(self):
        threads_enter()
        self.button_go.set_sensitive(1)
        threads_leave()

    def ui_set_next_step(self):
        self.cue_list.unselect_all()
        self.label_next.set_text('Next: ---')
        threads_enter()
        if (self.get_next_step()):
            #self.cue_list.disconnect(self.cue_list_handler_id)

            self.label_next.set_text('Next: '+self.get_next_step().name)
            self.cue_list.select_item(self.next_step)

            #self.cue_list_handler_id=self.cue_list.connect('selection_changed', self.selection_changed, None)

        threads_leave()

    def stop_clicked(self, widget, data=None):
        pass

    def go_clicked(self, widget, data=None):
        self.step_forward()

    def selection_changed(self, widget, data=None):
        sel=widget.get_selection()
        if (not sel):
            return
        p=widget.child_position(sel[0])
        if (p==self.next_step):
            return
        threads_leave()
        self.set_next_step(p)
        threads_enter()

    def run_destroyed(self, widget, data=None):
        self.stop()
        self.run_menu_item.set_sensitive(1)        

    def run_cb(self, widget, data=None):
        """ Called from lightboard->program->run """

        self.run_menu_item.set_sensitive(0)
        threads_leave()
        self.create_window()
        threads_enter()

        threads_leave()
        self.run()
        threads_enter()
        
