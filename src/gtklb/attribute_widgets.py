import lightboard
import string
from gtk import *

class AttributeWidget:

    attribute=None
    
    def __init__(self):
        self.widget=None
        self.changed_callback=None

    def get_widget(self):
        return self.widget
    
    def get_string_value(self):
        pass

    def set_string_value(self, value):
        pass

    def get_core_value(self):
        pass

    def set_core_value(self, value):
        pass

    def changed(self, widget, *args):
        if (self.changed_callback):
            self.changed_callback(self)

    def set_sensitive(self, v):
        self.widget.set_sensitive(v)

    def string_to_core(v):
        pass

    def core_to_string(v):
        pass
    

def level_string_to_core(level):
    level=str(level)
    if (level[-1]=='%'):
        level=level[:-1]
    return [float(level)]

def level_core_to_string(pct):
    level=str(pct[0])+'%'
    return level
    
class LevelWidget(AttributeWidget):
    attribute='level'
    def __init__(self, value, changed_callback):
        AttributeWidget.__init__(self)
        self.changed_callback=changed_callback
        self.widget = GtkSpinButton()
        adj = self.widget.get_adjustment()
	adj.set_all(0.0, 0.0, 100.0, 1.0, 10.0, 10.0)
        adj.connect('value_changed', self.changed)
        self.set_string_value(value)
        self.widget.show()

    def get_string_value(self):
        v = self.widget.get_value_as_float()
        return level_core_to_string([v])

    def set_string_value(self, value):
        v = level_string_to_core(value)
        self.widget.set_value(v[0])

    def get_core_value(self):
        v = self.widget.get_value_as_float()
        return [v]

    def set_core_value(self, value):
        self.widget.set_value(v[0])


def time_string_to_core(time):
    try:
        time=float(time)
        return time
    except:
        time=str(time)
    if(string.lower(time[-1])=='s'):
        return float(time[:-1])
    if(string.lower(time[-1])=='m'):
        return float(time[:-1])*60
    if(string.lower(time[-1])=='h'):
        return float(time[:-1])*60*60
    ftime=0.0
    multiple=1.0
    l=string.rfind(time, ':')
    while (l!=-1):
        n=float(time[l+1:])
        ftime=ftime+(n*multiple)
        time=time[:l]
        multiple=multiple*60.0
        if (multiple>3600):
            return None
        l=string.rfind(time, ':')
    if (len(time)):
        ftime=ftime+(float(time)*multiple)
    return ftime

def time_core_to_string(str):
    pass
