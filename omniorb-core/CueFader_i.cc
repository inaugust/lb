//
// Example code for implementing IDL interfaces in file CueFader.idl
//

#include <iostream.h>
#include <CueFader.hh>

//
// Example class implementing IDL interface LB::CueFader
//
class LB_CueFader_i: public POA_LB::CueFader,
                public PortableServer::RefCountServantBase {
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_CueFader_i();
public:
  // standard constructor
  LB_CueFader_i();
  virtual ~LB_CueFader_i();

  // methods corresponding to defined IDL attributes and operations
  void setStartCue(const LB::Cue& incue);
  void setEndCue(const LB::Cue& incue);
  void setAttributes(const LB::AttrList& attr);
  void clear();
  char* name();
  void run(const char* level, const char* time);
  void stop();
  void setLevel(const char* level);
  CORBA::Boolean isRunning();
  
};

//
// Example implementational code for IDL interface LB::CueFader
//
LB_CueFader_i::LB_CueFader_i(){
  // add extra constructor code here
}
LB_CueFader_i::~LB_CueFader_i(){
  // add extra destructor code here
}
//   Methods corresponding to IDL attributes and operations
void LB_CueFader_i::setStartCue(const LB::Cue& incue){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_CueFader_i::setStartCue(const LB::Cue& incue)>"
}

void LB_CueFader_i::setEndCue(const LB::Cue& incue){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_CueFader_i::setEndCue(const LB::Cue& incue)>"
}

void LB_CueFader_i::setAttributes(const LB::AttrList& attr){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_CueFader_i::setAttributes(const LB::AttrList& attr)>"
}

void LB_CueFader_i::clear(){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_CueFader_i::clear()>"
}

char* LB_CueFader_i::name(){
  // insert code here and remove the warning
#warning "Code missing in function <char* LB_CueFader_i::name()>"
}

void LB_CueFader_i::run(const char* level, const char* time){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_CueFader_i::run(const char* level, const char* time)>"
}

void LB_CueFader_i::stop(){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_CueFader_i::stop()>"
}

void LB_CueFader_i::setLevel(const char* level){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_CueFader_i::setLevel(const char* level)>"
}

CORBA::Boolean LB_CueFader_i::isRunning(){
  // insert code here and remove the warning
#warning "Code missing in function <CORBA::Boolean LB_CueFader_i::isRunning()>"
}

// End of example implementational code
