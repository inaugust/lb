//
// Example code for implementing IDL interfaces in file Fader.idl
//

#include <iostream.h>
#include <Fader.hh>

//
// Example class implementing IDL interface LB::Fader
//
class LB_Fader_i: public POA_LB::Fader,
                public PortableServer::RefCountServantBase {
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_Fader_i();
public:
  // standard constructor
  LB_Fader_i();
  virtual ~LB_Fader_i();

  // methods corresponding to defined IDL attributes and operations
  char* name();
  void run(const char* level, const char* time);
  void stop();
  void setLevel(const char* level);
  CORBA::Boolean isRunning();
  
};

//
// Example implementational code for IDL interface LB::Fader
//
LB_Fader_i::LB_Fader_i(){
  // add extra constructor code here
}
LB_Fader_i::~LB_Fader_i(){
  // add extra destructor code here
}
//   Methods corresponding to IDL attributes and operations
char* LB_Fader_i::name(){
  // insert code here and remove the warning
#warning "Code missing in function <char* LB_Fader_i::name()>"
}

void LB_Fader_i::run(const char* level, const char* time){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_Fader_i::run(const char* level, const char* time)>"
}

void LB_Fader_i::stop(){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_Fader_i::stop()>"
}

void LB_Fader_i::setLevel(const char* level){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_Fader_i::setLevel(const char* level)>"
}

CORBA::Boolean LB_Fader_i::isRunning(){
  // insert code here and remove the warning
#warning "Code missing in function <CORBA::Boolean LB_Fader_i::isRunning()>"
}

// End of example implementational code
