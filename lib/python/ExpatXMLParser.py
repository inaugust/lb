from xml.parsers import expat

entitydefs = {'lt':'<', 'gt':'>', 'amp':'&', 'quote':'"', 'apos':"'"}

reverse_entitydefs={}
for k,v in entitydefs.items():
    reverse_entitydefs[v]=k

def reverse_translate_references(str):
    s = ''
    for c in str:
        if (c in reverse_entitydefs.keys()):
            c = '&'+reverse_entitydefs[c]+';'
        s=s+c
    return s

class ExpatXMLParser:

    def __init__(self):
        self.parser=expat.ParserCreate('ASCII')
        self.parser.StartElementHandler = self.magic_start_element
        self.parser.EndElementHandler = self.magic_end_element
        self.parser.CharacterDataHandler = self.char_data
        self.parser.returns_unicode=0
        self.Parse=self.parser.Parse

    def unknown_starttag(self, name, attrs):
        pass
    
    def magic_start_element(self, name, attrs):
        if hasattr(self, 'start_'+name):
            m=getattr(self, 'start_'+name)
            apply(m, [attrs])
        else:
            self.unknown_starttag(name, attrs)

    def unknown_endtag(self, name):
        pass

    def magic_end_element(self, name):
        if hasattr(self, 'end_'+name):
            m=getattr(self, 'end_'+name)
            apply(m, [])
        else:
            self.unknown_endtag(name)

    def char_data(self, data):
        if hasattr(self, 'handle_data'):
            m=getattr(self, 'handle_data')
            apply(m, [data])
        else:
            pass
    
    def close(self):
        # pesky circular refs:
        self.Parse = self.parser = None

class DOMNode:
    def __init__(self, tag=None, attrs={}):
##        self.tag=str(tag)
        self.tag=tag
        self.attrs = attrs
##        for k,v in self.attrs.items():
##             try:
##                 if type(k)==type(u'a'):
##                     del(self.attrs[k])
##                     k=str(k)
##                 if type(v)==type(u'a'):
##                     self.attrs[k]=str(v)
##             except:
##                 # Pre 2.1 we should get syntax error. But that's ok.
##                 # because pre 2.1 we don't need to do this.
##                 pass
            
        self.data = ''
        self.children=[]
        
    def append(self, child):
        if (child is not None):
            self.children.append(child)

    def add_data(self, data):
##         try:
##             if type(data)==type(u'a'):
##                 data=str(data)
##         except:
##             pass #Python pre-2.1 syntax error above. But that's ok.
        
        self.data = self.data + data

    def find(self, tag):
        r = []
        for n in self.children:
            if n.tag == tag:
                r.append(n)
        return r
