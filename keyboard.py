# This is just a hack.

from threading import *
from select import *
import sys, termios, TERMIOS
import process

SPACE=' '
oldtermios=None
terminated=0

def initialize(lb):
    global oldtermios
    
    fd = sys.stdin.fileno()
    oldtermios = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~(TERMIOS.ICANON | TERMIOS.ECHO)
    termios.tcsetattr(fd, TERMIOS.TCSANOW, new)

    lb.add_signal ('Key Press', handle_key_press)
    t=Thread (target=kbmonitor)
    t.start()

def shutdown():
    global terminated
    terminated=1
    fd = sys.stdin.fileno()
    termios.tcsetattr(fd, TERMIOS.TCSANOW, oldtermios)
    
def handle_key_press (args):
    global proc
    key = args['key']
    if (key==SPACE):
        lb.crossfader['AB'].get_fader('A').set_cue('1')
        lb.crossfader['AB'].get_fader('A').set_level('100%')
        lb.crossfader['AB'].get_fader('B').set_cue('2')
        lb.crossfader['AB'].get_fader('B').set_level('0%')
        lb.crossfader['AB'].run()
    if (key=='s'):
        lb.program['prog1'].run()
    if (key=='g'):
        lb.program['prog1'].step_forward()
    if (key=='p'):
        for e in lb.events:
            print e
        lb.events=[]
    if (key=='c'):
        proc=process.process()
        proc.start(lb.procedure['circle'], instrument='1', center=(10, 10), radius=5)
    if (key=='a'):
        proc.stop()
    if (key=='q'):
        lb.exit()
        
def kbmonitor ():
    while not terminated:
        try:
            (i,o,e)=select ([sys.stdin], [], [], 2)
        except Exception:
            lb.exit ()
        if sys.stdin in i:
          c=sys.stdin.read(1)
          lb.send_signal('Key Press', key=c)
    print 'kbmonitor exited'
