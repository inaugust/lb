#include <iostream.h>
#include "Lightboard_i.hh"
#include "Dimmer_i.hh"
#include "Instrument_i.hh"
#include "MovingInstrument_i.hh"
#include "Fader_i.hh"
#include "CueFader_i.hh"
#include "CrossFader_i.hh"
#include "LevelFader_i.hh"


//#include <CosEventChannelAdmin.hh>
//#include <EventChannelAdmin.hh>

LB::Lightboard_ptr lb;
CORBA::ORB_var orb;

int make_level(long int level)
{
  /* takes a percentage in .01 percent and returns 0-dimmerrange */
  return 0;
}

double make_time(const char *t)
{
  int len=strlen(t);
  char *tim=strdup(t);
  double  ftime=0.0;

  if(t[len-1]=='s')
    return atof(t);
  if(t[len-1]=='m')
    return atof(t)*60;
  if(t[len-1]=='h')
    return atof(t)*60*60;
  
  double  multiple=1.0;
  char *p=strrchr(tim, ':');

  while (p!=NULL)
    {
      double n=atof(p+1);
      ftime=ftime+(n*multiple);
      *p=0;
      multiple=multiple*60.0;
      if (multiple>3600)
	{
	  free(tim);
	  return 0;
	}
      p=strrchr(tim, ':');
    }
  if (strlen(tim))
    ftime=ftime+(atof(tim)*multiple);
  free(tim);
  return ftime;
}


LB::Cue *duplicate_cue (const LB::Cue& incue, int zero)
{
  LB::Cue *cue = new LB::Cue;

  cue->name = incue.name;
  int numins=incue.ins.length();
  cue->ins.length(numins);
  for (int i=0; i<numins; i++)
    {
      cue->ins[i].name = incue.ins[i].name;
      int numattr=incue.ins[i].attrs.length();
      cue->ins[i].attrs.length(numattr);
      for (int a=0; a<numattr; a++)
	{
	  cue->ins[i].attrs[a].attr=incue.ins[i].attrs[a].attr;
	  int numval=incue.ins[i].attrs[a].value.length();
	  cue->ins[i].attrs[a].value.length(numval);
	  for (int v=0; v<numval; v++)
	    {
	      if (zero)
		cue->ins[i].attrs[a].value[v]=0.0;

	      else
		cue->ins[i].attrs[a].value[v]=incue.ins[i].attrs[a].value[v];
	    }
	}
    }
  
  return cue;
}

CosNaming::NamingContext_ptr
getRootNamingContext(CORBA::ORB_ptr orb)
{
  CosNaming::NamingContext_ptr rootContext;
  try {

     // Get initial reference.
     CORBA::Object_var initServ;
     initServ = orb->resolve_initial_references("NameService");

     // Narrow the object returned by resolve_initial_references()
     // to a CosNaming::NamingContext object:
     rootContext = CosNaming::NamingContext::_narrow(initServ);
     if (CORBA::is_nil(rootContext))
     {
        cerr << "Failed to narrow naming context." << endl;
        exit(1);
     }
  }
  catch(CORBA::ORB::InvalidName& ex) {
     cerr << "Service required is invalid [does not exist]." << endl;
     exit(1);
  }
  catch (CORBA::COMM_FAILURE& ex) {
     cerr << "Caught system exception COMM_FAILURE."
          << endl;
     exit(1);
  }
  catch (omniORB::fatalException& ex) {
     cerr << "Caught Fatal Exception" << endl;
     throw;
  }
  catch (...) {
     cerr << "Caught a system exception while resolving the naming service."
          << endl;
     exit(1);
  }
  return rootContext;
}

static CORBA::Boolean
bindObjectToName(CORBA::ORB_ptr orb, CORBA::Object_ptr objref, 
                 const char* id, const char* kind)
{
  
  try { 
    CosNaming::NamingContext_ptr rootContext = getRootNamingContext(orb);
    
    // Bind objref with name Echo to the testContext:
    CosNaming::Name objectName;
    objectName.length(1);
    objectName[0].id   = id;   // string copied
    objectName[0].kind = kind; // string copied
    
    try {
      rootContext->bind(objectName, objref);
    }
    catch(CosNaming::NamingContext::AlreadyBound& ex) {
      rootContext->rebind(objectName, objref);
    }
  }
  catch(CORBA::COMM_FAILURE& ex) {
    cerr << "Caught system exception COMM_FAILURE -- unable to "
         << "contact the naming service." << endl;
    return 0;
  }
  catch(CORBA::SystemException&) {
    cerr << "Caught a CORBA::SystemException while using the "
         << "naming service." << endl;
    return 0;
  }
  return 1;
}

int main(int argc, char** argv)
{
  try {
    // Initialise the ORB.
    orb = CORBA::ORB_init(argc, argv, "omniORB3");

    // Obtain a reference to the root POA.
    CORBA::Object_var obj = orb->resolve_initial_references("RootPOA");
    PortableServer::POA_var poa = PortableServer::POA::_narrow(obj);

    // Obtain the Naming Service
    CosNaming::NamingContext_ptr namectx = getRootNamingContext(orb);


    // We allocate the objects on the heap.  Since these are reference
    // counted objects, they will be deleted by the POA when they are no
    // longer needed.
    LB_Lightboard_i* myLB_Lightboard_i = new LB_Lightboard_i();

    // Activate the objects.  This tells the POA that the objects are
    // ready to accept requests.
    PortableServer::ObjectId_var myLB_Lightboard_iid = poa->activate_object(myLB_Lightboard_i);
    

    // Obtain a reference to each object and output the stringified
    // IOR to stdout

    printf ("a\n");
    /*    {  */
      // IDL interface: LB::Lightboard
      lb = myLB_Lightboard_i->_this();

      // Register the object with the naming service.
      if( !bindObjectToName(orb, lb, "lb", "Lightboard") )
            return 1;

      {
      CORBA::String_var sior(orb->object_to_string(lb));
      cout << "IDL object LB::Lightboard IOR = '" << (char*)sior << "'" << endl;
      FILE *f = fopen ("/tmp/lb.ior", "w");
      fputs ((char *)sior, f);
      fputs ("\n", f);
      fclose (f);
      }
    printf ("a\n");
    // Obtain a POAManager, and tell the POA to start accepting
    // requests on its objects.
    PortableServer::POAManager_var pman = poa->the_POAManager();
    pman->activate();
    
    initialize_dimmers(lb);
    initialize_instruments(lb);
    initialize_moving_instruments(lb);
    initialize_faders(lb);
    initialize_cuefaders(lb);
    initialize_crossfaders(lb);
    initialize_levelfaders(lb);


    //    CORBA::Object_var obj = rootContext->resolve(name);

    orb->run();
    orb->destroy();
  }
  catch(CORBA::SystemException&) {
    cerr << "Caught CORBA::SystemException." << endl;
  }
  catch(CORBA::Exception&) {
    cerr << "Caught CORBA::Exception." << endl;
  }
  catch(omniORB::fatalException& fe) {
    cerr << "Caught omniORB::fatalException:" << endl;
    cerr << "  file: " << fe.file() << endl;
    cerr << "  line: " << fe.line() << endl;
    cerr << "  mesg: " << fe.errmsg() << endl;
  }
  catch(...) {
    cerr << "Caught unknown exception." << endl;
  }

  return 0;
}
