# This is just a hack.

from threading import *
from select import *
import sys, termios, TERMIOS, string
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
    if (key>='1' and key<='9'):
        lb.foo_program_name='prog'+str(key)
        lb.program[lb.foo_program_name].run()
    if (key=='?'):
        print lb.program.keys()
    if (key=='o'):
        print "Which step?"
        stps=map(lambda x: x.name, lb.program[lb.foo_program_name].actions)
        print stps
        q=string.strip(sys.stdin.readline())
        print q
        lb.program[lb.foo_program_name].set_next_step(step=stps.index(q))
        #lb.program[lb.foo_program_name].next_step=q
        #lb.program[lb.foo_program_name].step_forward()
    if (key=='g'):
        lb.program[lb.foo_program_name].step_forward()
    if (key=='p'):
        for e in lb.events:
            print e
        lb.events=[]
    if (key=='c'):
        proc=process.process()
        proc.start(lb.procedure['circle'], instrument='moving1', center=(10, 10), radius=5)
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
