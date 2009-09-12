#!/usr/bin/python

from threading import *
import socket
import sys

import gtk, gtk.glade

libraries=(
  'attribute_widgets',
  'program',
  'instrument',
  'color_mixer_instrument',
  'meta_instrument',
  'cue',
  'fader',
  'crossfader',
  'levelfader',
  'procedure',
  'process',
  )

from lightboard import lightboard

datafile = None
clientname = 'gtklb'

name = None
for arg in sys.argv[1:]:
  print arg
  if (name is None):
    name = arg
    continue
  else:
    value = arg
  print name,value
  if (name == '--client'):
    clientname = value
  if (name == '--show'):
    datafile = value
  name = None
    

def gtk_main():
  gtk.gdk.threads_enter()
  gtk.main()
  gtk.gdk.threads_leave()

gtk.gdk.threads_init()

t=Thread (target=gtk_main)
t.start()

print clientname

lb = lightboard(clientname)
lb.load_libraries(libraries)
if (datafile is not None):
  lb.load_show(datafile)
lb.run()


