import lightboard
import string
from gtk import *
from types import *
import re

hex_table = {'0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8,
             '9':9, 'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15,
             'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15} 

rgb_table = {}

def initialize():
    global rgb_table
    p = re.compile("\s*(\S+)\s*(\S+)\s*(\S+)\s*(.*)")
    f = open ("/etc/X11/rgb.txt")
    while 1:
        l = f.readline()
        if (not l): break
        if (l[0]=='!'): continue
        m = p.match(l)
        r,g,b,n = m.group(1), m.group(2), m.group(3), m.group(4)
        rgb_table[n]=(float(r)/255.0, float(g)/255.0, float(b)/255.0)
    f.close()

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
    
#################
#
# Level
#
##################

def level_string_to_core(level):
    if (type(level) is not StringType):
        if (type(level) is not ListType):
            return [level]
        else:
            return level
    level=str(level)
    if not len(level):
        level='0%'
    if (level[-1]=='%'):
        level=level[:-1]
    return [float(level)]

def level_core_to_string(pct):
    if (type(pct) is not ListType):
        if (type(pct) is StringType):
            return pct
        else:
            pct=[pct]
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

##################
#
# Time
#
##################

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

####################
#
# Color (RGB)
#
####################

def color_string_to_core(color):
    if (type(color) is not StringType):
        return color
    if not len(color):
        return [100.0, 100.0, 100.0]
    if color[0]=='#':
        # hex triplet
        r = color[1:3]
        g = color[3:5]
        b = color[5:7]
        r = (hex_table[r[0]]*16 + hex_table[r[1]])/255.0*100.0
        g = (hex_table[g[0]]*16 + hex_table[g[1]])/255.0*100.0
        b = (hex_table[b[0]]*16 + hex_table[b[1]])/255.0*100.0
    else:
        # try rgb.txt
        try:
            (r,g,b) = rgb_table[color]
        except:
            (r,g,b) = (100.0, 100.0, 100.0)
    return [r,g,b]

def color_core_to_string(color):
    if (type(color) is not ListType):
        return color
    s = '#%02x%02x%02x' % (int(color[0]/100.0*255), int(color[1]/100.0*255), int(color[2]/100.0*255))
    return s
    
class ColorWidget(AttributeWidget):
    attribute='color'
    def __init__(self, value, changed_callback):
        AttributeWidget.__init__(self)
        self.changed_callback=changed_callback
        self.widget = GtkColorSelection()
        self.widget.connect('color_changed', self.changed)
        self.set_string_value(value)
        self.widget.show()

    def get_string_value(self):
        v = self.get_core_value()
        return color_core_to_string(v)

    def set_string_value(self, value):
        (r,g,b) = color_string_to_core(value)
        self.set_core_value([r,g,b])

    def get_core_value(self):
        c = self.widget.get_color()
        (r,g,b) = (c[0]*100.0, c[1]*100.0, c[2]*100.0)
        return [r,g,b]

    def set_core_value(self, value):
        c = (int(value[0]/100.0), int(value[1]/100.0), int(value[2]/100.0))
        self.widget.set_color(c)
