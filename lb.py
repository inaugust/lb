#!/usr/bin/python

from Numeric import *

libraries=(
    'dimmer',
    'instrument',
    'moving_instrument',
    'cue',
    'levelfader',
    'crossfader',
    'program',
    'procedure',
    'process',
    'keyboard',
#    'gtkui',
    )

from lightboard import lightboard

show='show'

lb = lightboard(show)
lb.load_libraries(libraries)
lb.start()

