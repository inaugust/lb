#!/usr/bin/python

from threading import *
import socket
import sys

import gtk

libraries=(
  'instrument',
  'cue',
  'fader',
  'crossfader',
  'levelfader',
  'program',
  'procedure',
  'process',
#  'keyboard',
  )

from lightboard import lightboard

if (len(sys.argv)>1):
  datafile = sys.argv[1]
else:
  datafile = None
  
clientname='gtklb1'

def gtk_main():
  gtk.threads_enter()
  gtk.mainloop()
  gtk.threads_leave()

t=Thread (target=gtk_main)
t.start()

lb = lightboard(clientname)
lb.load_libraries(libraries)
if (datafile is not None):
  lb.load_show(datafile)
lb.run()


