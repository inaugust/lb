#!/usr/bin/python

libraries=(
    'dimmer',
    'instrument',
    'moving_instrument',
    'cue',
    'fader',
    'crossfader',
    'program',
    'procedure',
    'process',
    'keyboard',
    )

from lightboard import lightboard

show='show'

lb = lightboard(show)
lb.load_libraries(libraries)
lb.start()

