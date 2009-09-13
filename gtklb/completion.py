import sys
import string
import time
import __builtin__
import __main__
import types
import code
import re
from codeop import compile_command
from gtk import *

def find_space(text):
    balancing = {
        '"' : '"',
        "'" : "'",
        }
    
    unbalanced=[]

    count = 0
    prev = ''
    lastspace=None
    for l in text:
        count = count+1
        if l in balancing.values():
            if len(unbalanced) != 0:
                if balancing[unbalanced[-1]] == l:
                    unbalanced.pop()
                else:
                    unbalanced.append(l)
            else:
                unbalanced.append(l)                
        elif l in balancing.keys():
            unbalanced.append(l)
        if l==' ' and prev!='\\':
            if len(unbalanced) == 0:
                lastspace = count
        prev = l
    return lastspace

class completion(code.InteractiveConsole):
    def __init__(self, locals):
        code.InteractiveConsole.__init__(self, locals)
        self.completion_dicts = [locals]
        
        self.command_history=[]
        self.command_history_index=-1
        self.complete_state=0


    def completion_global_matches(self, text):
        """ From rlcompleter.py
        Compute matches when text is a simple name.

        Return a list of all keywords, built-in functions and names
        currently defines in __main__ that match.
        """

        matches = []
        n = len(text)

        #keyword.kwlist,
        #__builtin__.__dict__.keys(),
        #__main__.__dict__.keys(),

        for list in self.completion_dicts:
            for word in list.keys():
                if word[:n] == text and word[0]!='_':
                    matches.append(word)
        return matches

    def completion_attr_matches(self, text):
        """ From rlcompleter.py
        Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluabable in the globals of __main__, it will be evaluated
        and its attributes (as revealed by dir()) are used as possible
        completions.

        WARNING: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.

        """

        matches = []
        initial_quote = "'"

        #m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        m = re.match(r"([\w\.\[\]\'\"]*)((\[([\'\"\w]*))|(\.(\w*)))", text)
        if not m:
            return []

        expr, item, attr = m.group(1, 4, 6)
        if item:
            if item[0]=='"':
                initial_quote = '"'
                item = item[1:]
            elif item[0]=="'":
                item = item[1:]
        
        words = []
        
        if (item!=None):
            i=None
            for dict in self.completion_dicts:
                try:
                    i=eval(expr, dict)
                except:
                    pass
                if i:
                    break
            if (not i): 
                return []
            if (type(i)==type([])):
                words=words+map(str, range(0, len(i)))
                t=0
            if (type(i)==type({})):
                words=words+i.keys()
                t=1
            words.sort()
            n = len(item)
            for word in words:
                if word[:n] == item:
                    if (t):
                        matches.append("%s[%s%s%s]" % (expr, initial_quote, word, initial_quote))
                    else:
                        matches.append("%s[%s]" % (expr, word))
                
        elif (attr!=None):
            i=None
            for dict in self.completion_dicts:
                try:
                    i=eval(expr, dict)
                except:
                    pass
                if i:
                    break
            if (not i): 
                return []
            for word in dir(i):
                if (word[0] != '_'):
                    words.append(word)
            if (type(i) == types.InstanceType):
                for word in dir(i.__class__):
                    if (word[0] != '_'):
                        words.append(word)
                for base in i.__class__.__bases__:
                    for word in dir(base):
                        if (word[0] != '_'):
                            words.append(word)
            words.sort()
            n = len(attr)
            for word in words:
                if word[:n] == attr:
                    matches.append("%s.%s" % (expr, word))
            
        return matches

    def completion_matches(self, text):
        """ From rlcompleter.py
        """
        lastword = text
        loc = find_space(text)
        if loc:
            lastword = text[loc:]
            
        while (lastword[0] == '('):
            loc = loc+1
            lastword = lastword[1:]
        if "." in text or "[" in lastword:
            matches = self.completion_attr_matches(lastword)
        else:
            matches = self.completion_global_matches(lastword)
        rmatches=[]
        for match in matches:
            match = text[:loc]+match
            if match not in rmatches:
                rmatches.append(match)
        return rmatches

    def completion_unambiguous_chars(self, text, matches):
        if (len(matches)<1):
            return ''
        chars=matches[0]
        for match in matches[1:]:
            if (len(chars)==0):
                return ''
            for p in range (0, len(chars)):
                if (chars[p] != match[p]):
                    chars=chars[:p]
                    break
        return chars[len(text):]

### UI stuff
    
    def key_pressed(self, widget, event, data=None):
        handled=0
        if (event.keyval==gtk.gdk.Tab):
            handled=1
            alltext = widget.get_text()
            text = alltext[:widget.get_position()]
            rest = alltext[widget.get_position():]

            matches=self.completion_matches(text)
            chars = self.completion_unambiguous_chars(text, matches)
            text=text+chars
            widget.set_text(text+rest)
            matches=self.completion_matches(text)

            if (len(matches)>1):
                if (self.complete_state):
                    self.textbox.insert_defaults("Completions:\n")
                    self.textbox.insert_defaults(str(matches) +"\n")
                else:
                    self.complete_state=1
        else:
            self.complete_state=0

        if (event.keyval==gtk.gdk.Up or
            event.keyval==gtk.gdk.KP_Up ):
            handled=1
            if (len(self.command_history) and
                self.command_history_index+1 < len(self.command_history)):
                self.command_history_index=self.command_history_index+1
                widget.set_text(self.command_history[self.command_history_index])

        if (event.keyval==gtk.gdk.Down or
            event.keyval==gtk.gdk.KP_Down ):
            handled=1
            if (self.command_history_index > -1):
                self.command_history_index=self.command_history_index-1
                if (self.command_history_index == -1):
                    widget.set_text("")
                else:
                    widget.set_text(self.command_history[self.command_history_index])

        if (handled):
            # This keeps the widget from handling it...
            widget.emit_stop_by_name('key_press_event')
            # This keeps GTK from handling it.
            return 1
        return 0
        
    def entry_activated(self, widget, data=None):
        #widget.freeze()

        command = widget.get_text()
        widget.set_text("")

        self.command_history.insert(0, command)
        self.command_history_index=-1

        old = sys.stdout

        gdk.threads_leave()
        self.write(">>> "+command+"\n")
        sys.stdout=self
        r=self.push(command)
        sys.stdout=old
        gdk.threads_enter()

        if (r):
            self.more_toggle.set_active(1)
        else:
            self.more_toggle.set_active(0)
            
        #widget.thaw()

    def write(self, data):
        """ Write interpreter output """
        gdk.threads_enter()
        self.textbox.get_buffer().insert_at_cursor(data)
        gdk.threads_leave()
