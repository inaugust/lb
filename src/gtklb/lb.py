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
  'program',
  'procedure',
  'process',
#  'keyboard',
  )

from lightboard import lightboard

show='unnamed'
clientname='gtklb1'

def gtk_main():
  gtk.threads_enter()
  gtk.mainloop()
  gtk.threads_leave()

t=Thread (target=gtk_main)
t.start()

lb = lightboard(show, clientname)
lb.load_libraries(libraries)
lb.run()


