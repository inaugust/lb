import CORBA
import CosNaming

orb=CORBA.ORB_init([''],CORBA.ORB_ID)
print orb
name=orb.resolve_initial_references('NameService')._narrow(CosNaming.NamingContext)
print name
namelist=name.list(2)
print namelist
for n in namelist[0]:
  print n.binding_name[0].id
