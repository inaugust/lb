from threading import *
from xmllib import XMLParser
from os import path
import string
import process
from ExpatXMLParser import ExpatXMLParser, DOMNode
import time
from gtk import *
import GDK
from libglade import *
import crossfader
import levelfader

run_menu=None
edit_menu=None

def format_step(name, arg_dict):
    k = arg_dict.keys()
    k.sort()
    str=name
    for arg in k:
        str=str+"  "+arg + " = " + arg_dict[arg]
    return str

def initialize():
    lb.program_action_type = {}
    reset()

def reset():
    global run_menu
    global edit_menu
    lb.program={}
    lb.program_clipboard = None
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

    new1=GtkMenuItem("New With Druid")
    new1.connect("activate", newDruid_cb, None)
    program1_menu.append(new1)

    menubar.show_all()
    threads_leave()
    
def shutdown():
    for p in lb.program.values():
        p.stop()

def load(tree):
    for section in tree.find("programs"):
        for pgam in section.find("program"):
            p=Program (pgam.attrs['name'])
            for init in pgam.find("init"):
                s=Step(p)
                s.name='<init>'
                p.init_step=s
                for action in init.children:
                    kind=string.lower(action.tag)
                    a = Action(p)
                    a.kind = kind
                    a.args = action.attrs
                    s.actions.append (a)
            for step in pgam.find("step"):
                s = Step (p)
                s.name=step.attrs['name']
                p.actions.append(s)
                for action in step.children:
                    kind=string.lower(action.tag)
                    a = Action(p)
                    a.kind = kind
                    a.args = action.attrs
                    s.actions.append (a)

def save():
    tree = DOMNode('programs')
    for p in lb.program.values():
        tree.append(p.to_tree())
    return tree

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
        if (string.strip(name) != ''):
            if not lb.program.has_key(name):
                threads_leave()
                p=Program(name)
                p.send_update()
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

def newDruid_cb(widget, data=None):
    # called from menu
    threads_leave()
    f = programDruid()
    threads_enter()
    # that's it.

class Action:
    def __init__(self, my_prog):
        self.program = my_prog
        self.kind = 'no-op'
        self.args = {}

    def copy(self):
        s = Action(self.program)
        s.kind = self.kind
        s.args = self.args.copy()
        return s
    
    def window_change(self, widget=None, data=None):
        menu = self.editTree.get_widget("actionTypeMenu")
        name = menu.children()[0].get()
        args = lb.program_action_type[name][1]
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
                menu.show_all()
                entry.set_menu(menu)
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
            align = GtkAlignment(0.0, 0.5, 0.0, 0.0)
            align.add(entry)
            align.show()
            self.entryWidgets.append(entry)
            table.attach(align, 1, 2, x, x+1, xoptions=FILL, yoptions=0)

    def ok_clicked(self, widget, data=None):
        menu = self.editTree.get_widget("actionTypeMenu")
        win = self.editTree.get_widget("programActionEdit")
        name = menu.children()[0].get()
        args = lb.program_action_type[name][1]
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
        l = lb.program_action_type.keys()
        l.sort()
        for t in l:
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
        return win

class Step:
    def __init__(self, my_prog):
        self.program = my_prog
        self.name=''
        self.actions=[]

    def copy(self):
        s = Step(self.program)
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
        return win

class Program:

    def __init__(self, name):
        self.name=name
        self.init_step=Step(self)
        self.init_step.name='<init>'
        self.actions=[]
        self.current_step=None
        self.next_step=None
        self.processes={}
        self.mythread=None
        self.joining = 0
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
            self.running = 0
            self.joining = 1
            self.steplock.release()
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
            self.mythread = None
            self.joining = 0
        self.running=1
        self.steplock=Semaphore (0)
        self.current_step=None
        self.set_next_step(0)
        self.run_actions(self.init_step.actions)
        self.mythread=Thread (target=Program.do_run, args=(self,
                                                           self.actions))
        self.mythread.start()
        self.threadlock.release()

    def stop (self):
        self.threadlock.acquire()
        if (self.mythread):
            self.running = 0
            self.joining = 1
            self.steplock.release()
            self.threadlock.release()
            self.mythread.join()
            self.threadlock.acquire()
            self.mythread = None
            self.joining = 0
        self.threadlock.release()
        
    def step_forward (self):
        self.steplock.release()

    def set_next_step (self, step):
        self.stepnumlock.acquire()
        self.next_step=step
        self.ui_set_next_step()
        self.stepnumlock.release()

    def to_tree(self):
        program = DOMNode('program', {'name':self.name})
        init = DOMNode('init')
        program.append(init)
        for act in self.init_step.actions:
            action = DOMNode(act.kind, act.args)
            init.append(action)
        for stp in self.actions:
            step = DOMNode('step', {'name':stp.name})
            program.append(step)
            for act in stp.actions:
                action = DOMNode(act.kind, act.args)
                step.append(action)
        return program

    def send_update(self):
        tree = DOMNode('programs')
        tree.append(self.to_tree())
        lb.sendData(tree)

    # private

    def do_run (self, actions):
        self.run_steps ()
        if not self.joining:
            self.threadlock.acquire()
            self.mythread=None
            self.threadlock.release()

    def run_steps (self):        
        while (1):
            self.steplock.acquire()
            if (not self.running):
                return
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
        m = lb.program_action_type[action][0]
        m(args)

    # UI methods

    def edit_add_step_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        s = Step(self)
        s.name = "<unnamed>"
        node = tree.insert_node(None, current.sibling, [s.name],
                                is_leaf=FALSE)
        tree.node_set_row_data(node, s)
        self.child_windows.append(s.edit())

    def edit_add_action_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        act = Action(self)
        if (current.level == 1):
            parent = current
            sibling = None
        else:
            parent = current.parent
            sibling = current.sibling
        node = tree.insert_node(parent, sibling, [act.kind],
                                is_leaf=TRUE)
        tree.node_set_row_data(node, act)
        self.child_windows.append(act.edit())
            
    def edit_remove_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        tree.remove_node(current)

    def edit_edit_clicked(self, widget, data=None):
        tree=self.editTree.get_widget("programTree")
        current = tree.selection[0]
        n = tree.node_get_row_data(current)
        self.child_windows.append(n.edit())

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
            n=tree.insert_node(stepNode, None, [str], is_leaf=TRUE)
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
        self.init_step = Step(self)
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
        self.send_update()
        
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
        for w in self.child_windows:
            w.destroy()

    def popup_edit_activated(self, widget, data=None):
        tree = self.editTree.get_widget ("programTree")
        obj = tree.node_get_row_data(self.popup_node)
        self.child_windows.append(obj.edit())

    def popup_cut_activated(self, widget, data=None):
        tree = self.editTree.get_widget ("programTree")
        obj = tree.node_get_row_data(self.popup_node)
        children = []
        if self.popup_node.level == 1:
            for child in self.popup_node.children:
                children.append(tree.node_get_row_data(child))
        lb.program_clipboard = (self.popup_node.level, obj, children)
        tree.remove_node(self.popup_node)
        
    def popup_copy_activated(self, widget, data=None):
        tree = self.editTree.get_widget ("programTree")
        obj = tree.node_get_row_data(self.popup_node)
        children = []
        if self.popup_node.level == 1:
            for child in self.popup_node.children:
                children.append(tree.node_get_row_data(child))
        lb.program_clipboard = (self.popup_node.level, obj, children)
        
    def popup_paste_activated(self, widget, data=None):
        if (lb.program_clipboard == None):
            return
        tree = self.editTree.get_widget ("programTree")
        cb_node_level = lb.program_clipboard[0]
        cur_node = self.popup_node
        cb_obj = lb.program_clipboard[1]
        cb_children = lb.program_clipboard[2]
        if cb_node_level == 1 and cur_node.level==1:
            #step into step, gets inserted after step
            str = format_step (cb_obj.name, {})
            parent_node = tree.insert_node(None, cur_node, [str],
                                           is_leaf=FALSE)
            tree.node_set_row_data(parent_node, cb_obj.copy())
            for a in cb_children:
                str = format_step (a.kind, a.args)
                node = tree.insert_node(parent_node, None, [str],
                                        is_leaf=TRUE)
                tree.node_set_row_data(node, a.copy())
        if cb_node_level == 2 and cur_node.level==1:
            #action into step, gets inserted at end of step
            str = format_step (cb_obj.kind, cb_obj.args)
            node = tree.insert_node(cur_node, None, [str], is_leaf=TRUE)
            tree.node_set_row_data(node, cb_obj.copy())
        if cb_node_level == 2 and cur_node.level==2:
            #action into action, gets inserted after action
            str = format_step (cb_obj.kind, cb_obj.args)
            node = tree.insert_node(cur_node.parent, cur_node, [str],
                                    is_leaf=TRUE)
            tree.node_set_row_data(node, cb_obj.copy())

    def popup_delete_activated(self, widget, data=None):
        tree = self.editTree.get_widget ("programTree")
        tree.remove_node(self.popup_node)

    def popup_handler (self, widget, event):
        if (event.type == GDK.BUTTON_PRESS):
            if (event.button == 3):
                (row, col) =  widget.get_selection_info (event.x, event.y)
                self.popup_node=widget.node_nth(row)
                self.popup_menu.popup (None, None, None, 
                                       event.button, event.time);
                return 1
        return 0
    
    def edit(self):
        self.child_windows = []
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
            menu = GtkMenu()
            i=GtkMenuItem("Edit")
            i.connect("activate", self.popup_edit_activated, None)
            menu.append(i)
            i=GtkMenuItem("Cut")
            i.connect("activate", self.popup_cut_activated, None)
            menu.append(i)
            i=GtkMenuItem("Copy")
            i.connect("activate", self.popup_copy_activated, None)
            menu.append(i)
            i=GtkMenuItem("Paste")
            i.connect("activate", self.popup_paste_activated, None)
            menu.append(i)
            i=GtkMenuItem("Delete")
            i.connect("activate", self.popup_delete_activated, None)
            menu.append(i)
            menu.show_all()
            self.popup_menu = menu
            w.connect("button_press_event", self.popup_handler)

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
        threads_enter()
        self.cue_list.unselect_all()
        self.label_next.set_text('Next: ---')
        if (self.get_next_step()):
            #self.cue_list.disconnect(self.cue_list_handler_id)

            self.label_next.set_text('Next: '+self.get_next_step().name)
            self.cue_list.select_item(self.next_step)
            self.cue_list.scroll_vertical(SCROLL_JUMP, float(self.next_step)/float(len(self.actions)))

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
        self.run()
        threads_enter()

    
class programDruid:

    target = [('text/cuename',0,-1)]
    
    def __init__(self):
        threads_enter()
        try:
            wTree = GladeXML ("gtklb.glade",
                              "programDruid")
            
            dic = {"on_ok_clicked": self.ok_clicked,
                   "on_cancel_clicked": self.cancel_clicked,
                   "on_add_clicked": self.add_clicked,
                   "on_remove_clicked": self.remove_clicked,
                   }
            
            wTree.signal_autoconnect (dic)

            tree = wTree.get_widget("cueTree")
            
            cues = lb.cue.keys()
            cues.sort()
            for c in cues:
                tree.insert_node(None, None, [c], is_leaf=TRUE)

            tree = wTree.get_widget("programTree")
            tree.set_reorderable(1)

            optionMenu = wTree.get_widget("faderMenu")
            menu=GtkMenu()
            faders = lb.crossfader.keys() + lb.levelfader.keys()
            faders.sort()
            for f in faders:
                i=GtkMenuItem(f)
                i.show()
                menu.append(i)
            menu.show_all()
            optionMenu.set_menu(menu)
            optionMenu.set_history(0)
            menu.show()

            self.newTree=wTree
        finally:
            threads_leave()
    
    def ok_clicked(self, widget, data=None):
        window = self.newTree.get_widget("programDruid")
        ptree = self.newTree.get_widget("programTree")
        e = self.newTree.get_widget("nameEntry")
        name = e.get_text()
        if (string.strip(name) != ''):        
            if not lb.program.has_key(name):
                threads_leave()
                fader_name = self.newTree.get_widget('faderMenu').children()[0].get()
                fade_time = self.newTree.get_widget('timeEntry').get_text()
                try:
                    f = lb.crossfader[fader_name]
                except:
                    try:
                        f = lb.levelfader[fader_name]
                    except:
                        pass

                p=Program(name)
                if (isinstance (f, crossfader.CrossFader)):
                    load_action = Action(p)
                    load_action.kind='crossfader_load'
                    load_action.args={'crossfader': fader_name}
                    run_action = Action(p)
                    run_action.kind='crossfader_run'
                    run_action.args={'crossfader': fader_name,
                                      'uptime': fade_time,
                                      'downtime': fade_time}
                if (isinstance (f, levelfader.LevelFader)):
                    load_action = Action(p)
                    load_action.kind='levelfader_load'
                    load_action.args={'levelfader': fader_name}
                    run_action = Action(p)
                    run_action.kind='levelfader_run'
                    run_action.args={'levelfader': fader_name,
                                      'time': fade_time}
                count = 1
                for n in ptree.base_nodes():
                    cue_name = ptree.get_node_info(n)[0]
                    s = Step(p)
                    s.actions = [load_action.copy(), run_action.copy()]
                    s.actions[0].args['cue']=cue_name
                    s.name = 'Cue %i [%s]' % (count, cue_name)
                    count = count + 1
                    p.actions.append(s)
                p.send_update()
                threads_enter()
        window.destroy()
    
    def cancel_clicked(self, widget, data=None):
        w = self.newTree.get_widget("programDruid")
        w.destroy()

    def add_clicked(self, widget, data=None):
        ctree = self.newTree.get_widget("cueTree")
        ptree = self.newTree.get_widget("programTree")
        for n in ctree.selection:
            name = ctree.get_node_info(n)[0]
            ptree.insert_node(None, None, [name], is_leaf=TRUE)

    def remove_clicked(self, widget, data=None):
        ptree = self.newTree.get_widget("programTree")
        for n in ptree.selection:
            ptree.remove_node(n)

    
