#!/usr/bin/python

from threading import *
import socket
import sys

import gtk

libraries=(
    'cue',
    'crossfader',
    'program',
    'procedure',
    'process',
    'keyboard',
#    'gtkui',
    )

from lightboard import lightboard

show='show'

def gtk_main():
  gtk.threads_enter()
  gtk.mainloop()
  gtk.threads_leave()

t=Thread (target=gtk_main)
t.start()

lb = lightboard(show)
lb.load_libraries(libraries)
lb.run()


