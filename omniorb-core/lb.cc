#include <iostream.h>
#include "Lightboard_i.hh"
#include "Dimmer_i.hh"
#include "Instrument_i.hh"
#include "MovingInstrument_i.hh"
#include "Fader_i.hh"
#include "CueFader_i.hh"


#include <CosEventChannelAdmin.hh>
//#include <EventChannelAdmin.hh>
extern CosNaming::NamingContext_ptr getRootNamingContext(CORBA::ORB_ptr orb);


LB::Lightboard_ptr lb;

int make_level(long int level)
{
  /* takes a percentage in .01 percent and returns 0-dimmerrange */
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


int main(int argc, char** argv)
{
  try {
    // Initialise the ORB.
    CORBA::ORB_var orb = CORBA::ORB_init(argc, argv, "omniORB3");

    // Obtain a reference to the root POA.
    CORBA::Object_var obj = orb->resolve_initial_references("RootPOA");
    PortableServer::POA_var poa = PortableServer::POA::_narrow(obj);

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


    /************** events **************/



    char *channelName = (char *) "EventChannel";
    char *channelKind = (char *) "EventChannel";
    char *factoryName = (char *) "EventChannelFactory";
    char *factoryKind = (char *) "EventChannelFactory";
    CORBA::ULong pullRetryPeriod = 1;
    CORBA::ULong maxQueueLength = 0;
    CORBA::ULong maxEventsPerConsumer = 0;
    
    CosNaming::NamingContext_ptr rootContext;
    rootContext = getRootNamingContext(orb);
    


    /************** events **************/



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

