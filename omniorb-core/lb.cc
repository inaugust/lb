#include <iostream.h>
#include "Lightboard_i.hh"
#include "Dimmer_i.hh"
#include "Instrument_i.hh"
#include "MovingInstrument_i.hh"
#include "Fader_i.hh"
#include "CueFader_i.hh"


#include <CosEventChannelAdmin.hh>
#include <EventChannelAdmin.hh>

//extern CosNaming::NamingContext_ptr getRootNamingContext(CORBA::ORB_ptr orb);

LB::Lightboard_ptr lb;
CosEventChannelAdmin::ProxyPushConsumer_ptr proxy_consumer;

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
    
    EventChannelAdmin::EventChannelFactory_ptr factory;
    CosNaming::Name name;
    name.length (1);
    name[0].id = CORBA::string_dup (factoryName);
    name[0].kind = CORBA::string_dup (factoryKind);

    try 
      {
	CORBA::Object_var obj = rootContext->resolve(name);
	factory = EventChannelAdmin::EventChannelFactory::_narrow(obj);
	if (CORBA::is_nil(factory))
	  {
	    cerr << "Failed to narrow Event Channel Factory reference." << endl;
	    exit(1);
	  }
	
      }
    catch (CORBA::COMM_FAILURE& ex) {
      cerr << "Caught system exception COMM_FAILURE, unable to contact the "
	   << "naming service." << endl;
      exit(1);
    }
    catch (omniORB::fatalException& ex) {
      cerr << "Caught Fatal Exception" << endl;
      throw;
    }
    catch (...) {
      cerr << "Cannot find event channel factory ! [\""
	   << factoryName << "\", \"" << factoryKind << "\"]"
	   << endl;
      exit (1);
    }

    // Check that the factory is of the right type
    CosLifeCycle::Key key;
    key.length (1);
    key[0].id = CORBA::string_dup ("EventChannel");
    key[0].kind = CORBA::string_dup ("object interface");
    try {
      if (! factory->supports(key))
	{
	  cerr << "Factory does not support Event Channel Interface ! [\""
	       << factoryName << "\", \"" << factoryKind << "\"]"
	       << endl;
	  exit (1);
	}
    }
    catch (...)
      {
	cerr << "Failure contacting Event Channel Factory" << endl;
	exit (1);
      }  
    
    //
    // Create Event Channel Object.
    CosEventChannelAdmin::EventChannel_var channel;
    try {
      CORBA::Object_var channelObj;
      CosLifeCycle::Criteria criteria;
      criteria.length (3);
      criteria[0].name = CORBA::string_dup ("PullRetryPeriod");
      criteria[0].value <<= (CORBA::ULong) pullRetryPeriod;
      criteria[1].name = CORBA::string_dup ("MaxEventsPerConsumer");
      criteria[1].value <<= (CORBA::ULong) maxEventsPerConsumer;
      criteria[2].name = CORBA::string_dup ("MaxQueueLength");
      criteria[2].value <<= (CORBA::ULong) maxQueueLength;
      
      channelObj = factory->create_object(key, criteria);
      if (CORBA::is_nil(channelObj))
	{
	  cerr << "Channel Factory returned nil reference. ! [\""
	       << channelName << "\", \"" << channelKind << "\"]"
	       << endl;
	  exit(1);
	}
      
      // Narrow object returned to an Event Channel
      channel = CosEventChannelAdmin::EventChannel::_narrow(channelObj);
      if (CORBA::is_nil(channel))
	{
	  cerr << "Failed to narrow Event Channel ! [\""
	       << channelName << "\", \"" << channelKind << "\"]"
	       << endl;
	  exit(1);
	}
    }
    catch (CosLifeCycle::NoFactory& ex) {
      cerr << "Failed to create Event Channel : "
	   << "Interface not supported "
	   << endl;
      exit(1);
    }
    catch (CosLifeCycle::CannotMeetCriteria& ex) {
      cerr << "Failed to create Event Channel : "
	   << "Cannot meet Criteria "
	   << endl;
      exit(1);
    }
    catch (...) {
      cerr << "Failed to create Event Channel ! [\""
	   << channelName << "\", \"" << channelKind << "\"]"
	   << endl;
      exit(1);
    }
    
    //
    // Register event channel with naming service
    name.length (1);
    name[0].id = CORBA::string_dup (channelName);
    name[0].kind = CORBA::string_dup (channelKind);
    try {
      rootContext->bind (name,
			 CosEventChannelAdmin::EventChannel::_duplicate(channel));
    }
    catch(CosNaming::NamingContext::AlreadyBound& ex) {
      rootContext->rebind(name,
			  CosEventChannelAdmin::EventChannel::_duplicate(channel));
    }
    catch (CORBA::COMM_FAILURE& ex) {
      cerr << "Caught system exception COMM_FAILURE, unable to contact the "
	   << "naming service." << endl;
      exit(1);
    }
    catch (omniORB::fatalException& ex) {
      cerr << "Caught Fatal Exception" << endl;
      throw;
    }
    catch (...) {
      cerr << "Cannot register event channel ! [\""
	   << channelName << "\", \"" << channelKind << "\"]"
	   << endl;
      exit (1);
    }

    /************** supplier ************/

    //
    // Get Supplier Admin interface - retrying on Comms Failure.
    CosEventChannelAdmin::SupplierAdmin_var supplier_admin;
    while (1)
      {
	try {
	  supplier_admin = channel->for_suppliers ();
	  if (CORBA::is_nil(supplier_admin))
	    {
	      cerr << "Event Channel returned nil Supplier Admin !."
		   << endl;
	      exit(1);
	    }
	  break;
	}
	catch (CORBA::COMM_FAILURE& ex) {
	  cerr << "Caught COMM_FAILURE Exception "
	       << "obtaining Supplier Admin !. Retrying..."
	       << endl;
	  continue;
	}
	catch (...) {
	  cerr << "Unexpected System Exeption. "
	       << "Failed to obtain Supplier Admin !"
	       << endl;
	  exit(1);
	}
      }
    cerr << "Obtained SupplierAdmin." << endl;
    
    //    while (1)
    //  {
    //
    // Get proxy consumer - retrying on Comms Failure.
    while (1)
      {
	try {
	  proxy_consumer = supplier_admin->obtain_push_consumer ();
	  if (CORBA::is_nil(proxy_consumer))
	    {
	      cerr << "Supplier Admin return nil proxy_consumer !."
		   << endl;
	      exit(1);
	    }
	  break;
	}
	catch (CORBA::COMM_FAILURE& ex) {
	  cerr << "Caught COMM_FAILURE Exception "
	       << "obtaining Push Consumer !. Retrying..."
	       << endl;
	  continue;
	}
	catch (...) {
	  cerr << "Unexpected System Exeption. "
	       << "Failed to obtain Proxy Consumer !"
	       << endl;
	  exit(1);
	}
      }
    cerr << "Obtained ProxyPushConsumer." << endl;

    proxy_consumer=proxy_consumer;

    //
    // Connect Push Supplier - retrying on Comms Failure.
    CosEventComm::PushSupplier_ptr sptr;
    sptr = CosEventComm::PushSupplier::_nil();
    
    while (1)
      {
	try {
	  proxy_consumer->connect_push_supplier(sptr);
	  break;
	}
	catch (CORBA::BAD_PARAM& ex) {
	  cerr << "Caught BAD_PARAM Exception connecting Push Supplier !"
	       << endl;
	  exit (1);
	}
	catch (CosEventChannelAdmin::AlreadyConnected& ex) {
	  cerr << "Pull Supplier already connected !"
	       << endl;
	  break;
	}
	catch (CORBA::COMM_FAILURE& ex) {
	  cerr << "Caught COMM_FAILURE Exception "
	       << "connecting Push Supplier !. Retrying..."
	       << endl;
	  continue;
	}
	catch (...) {
	  cerr << "Unexpected System Exception. "
	       << "Failed to connect Push Supplier !"
	       << endl;
	  exit (1);
	}
      }
    cerr << "Connected Push Supplier." << endl;
    
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

