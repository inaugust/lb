#!/usr/bin/python1.5

import time

import sys,os
os.environ['IDLPATH']=os.environ.get('IDLPATH','')+'/usr/share/idl:/usr/local/share/idl:../omniorb-core'
import CORBA
import CosNaming
import sys,string
from idl import LB, LB__POA

class pci(LB__POA.InstrumentLevelListener):
  def sendEvent (self, evt):
    #print "push!"
    pass

class dummy:
  pass

orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
poa = orb.resolve_initial_references("RootPOA")
nsi=orb.resolve_initial_references("NameService")
print nsi
ns = nsi._narrow(CosNaming.NamingContext)
print ns

x=CosNaming.NameComponent("lightboards","")
y=[x]
o = ns.resolve(y)

x=CosNaming.NameComponent("LB1","")
y=[x]
o = o.resolve(y)

x=CosNaming.NameComponent("dimmers","")
y=[x]
o = o.resolve(y)

s=time.time()
for x in range (1, 1024):
  x=CosNaming.NameComponent(str(x),"Dimmer")
  y=[x]
  z=o.resolve(y)
  
e=time.time()

print e-s

#f=open ("/tmp/lb.ior", "r")
#ior=f.readline()
#f.close()
#o = orb.string_to_object(ior)
print o

f = o.getFader('C1')
#f = f._narrow(LB.CueFader)
print f, dir(f)

for n in range(1,51):
  i = o.getInstrument(str(n))
  print i
  servant=pci()
  listener=servant._this()
  print listener
  #ior=orb.object_to_string(listener)
  #print "Reference for servant:", n
  i.addLevelListener(listener)

class dummy:
  pass

def test_ins():
  num_ins=50

  attr=dummy()
  attr.attr=LB.attr_level
  attr.value=[0.0]

  ilist=[]
  for x in range(1,num_ins):
    ins=dummy()
    ins.name=str(x)
    ins.attrs=[attr]
    ilist.append(ins)

  cue1=dummy()
  cue1.name='cue1'
  cue1.ins=ilist

  attr=dummy()
  attr.attr=LB.attr_level
  attr.value=[100.0]

  ilist=[]
  for x in range(1,num_ins):
    ins=dummy()
    ins.name=str(x)
    ins.attrs=[attr]
    ilist.append(ins)

  cue2=dummy()
  cue2.name='cue2'
  cue2.ins=ilist

  f.setStartCue(cue1)
  f.setEndCue(cue2)

  f.run(100.0, 1.0)


def test_mov_ins():
  num_ins=50

  attrs=[]

  attr=dummy()
  attr.attr=LB.attr_target
  attr.value=[100.0, 100.0, 0.0]
  attrs.append(attr)

  ilist=[]
  
  for x in range(1,num_ins):
    ins=dummy()
    ins.name='moving'+str(x)
    ins.attrs=attrs
    ilist.append(ins)
  
  cue1=dummy()
  cue1.name='cue1'
  cue1.ins=ilist

  attrs=[]
  attr=dummy()
  attr.attr=LB.attr_target
  attr.value=[100.0, 100.0, 0.0]
  attrs.append(attr)

  ilist=[]
  for x in range(1,num_ins):
    ins=dummy()
    ins.name='moving'+str(x)
    ins.attrs=attrs
    ilist.append(ins)

  cue2=dummy()
  cue2.name='cue2'
  cue2.ins=ilist

  f.setStartCue(cue1)
  f.setEndCue(cue2)

  f.run(100.0, 5.0)


test_ins()
poa._get_the_POAManager().activate()
orb.run()
