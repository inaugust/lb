//        On startup, the object reference is printed to cout as a
//        stringified IOR. This string should be used as the argument to 
//        the client.
//

#include <iostream.h>
#include "echo.hh"
#include <stdio.h>

class Test_Echo_i : public POA_Test::Echo,
	       public PortableServer::RefCountServantBase
{
public:
  inline Test_Echo_i() {}
  virtual ~Test_Echo_i() {}
  virtual char* echoString(const char* mesg);
  virtual void loseString(const char* mesg);
};


char* Test_Echo_i::echoString(const char* mesg)
{
  //printf("%s\n",mesg);
  return CORBA::string_dup(mesg);
}
void Test_Echo_i::loseString(const char* mesg)
{
  //printf("%s\n",mesg);
  char* newMsg = CORBA::string_dup(mesg);
  
}

//////////////////////////////////////////////////////////////////////

int main(int argc, char** argv)
{
  try {
    CORBA::ORB_var orb = CORBA::ORB_init(argc, argv, "omniORB3");

    CORBA::Object_var obj = orb->resolve_initial_references("RootPOA");
    PortableServer::POA_var poa = PortableServer::POA::_narrow(obj);

    Test_Echo_i* myecho = new Test_Echo_i();

    PortableServer::ObjectId_var myechoid = poa->activate_object(myecho);

    // Obtain a reference to the object, and print it out as a
    // stringified IOR.
    obj = myecho->_this();
    CORBA::String_var sior(orb->object_to_string(obj));
    cout << (char*)sior << endl;

    myecho->_remove_ref();

    PortableServer::POAManager_var pman = poa->the_POAManager();
    pman->activate();

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
