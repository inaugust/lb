//
// Example code for implementing IDL interfaces in file MovingInstrument.idl
//

#include <iostream.h>
#include <MovingInstrument.hh>

//
// Example class implementing IDL interface LB::MovingInstrument
//
class LB_MovingInstrument_i: public POA_LB::MovingInstrument,
                public PortableServer::RefCountServantBase {
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_MovingInstrument_i();
public:
  // standard constructor
  LB_MovingInstrument_i();
  virtual ~LB_MovingInstrument_i();

  // methods corresponding to defined IDL attributes and operations
  void setTarget(const char* target);
  char* getTarget();
  char* name();
  void setAttribute(const char* attr, const char* value);
  LB::AttrList* getAttributes();
  void setLevel(const char* level);
  char* getLevel();
  
};

//
// Example implementational code for IDL interface LB::MovingInstrument
//
LB_MovingInstrument_i::LB_MovingInstrument_i(){
  // add extra constructor code here
}
LB_MovingInstrument_i::~LB_MovingInstrument_i(){
  // add extra destructor code here
}
//   Methods corresponding to IDL attributes and operations
void LB_MovingInstrument_i::setTarget(const char* target){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_MovingInstrument_i::setTarget(const char* target)>"
}

char* LB_MovingInstrument_i::getTarget(){
  // insert code here and remove the warning
#warning "Code missing in function <char* LB_MovingInstrument_i::getTarget()>"
}

char* LB_MovingInstrument_i::name(){
  // insert code here and remove the warning
#warning "Code missing in function <char* LB_MovingInstrument_i::name()>"
}

void LB_MovingInstrument_i::setAttribute(const char* attr, const char* value){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_MovingInstrument_i::setAttribute(const char* attr, const char* value)>"
}

LB::AttrList* LB_MovingInstrument_i::getAttributes(){
  // insert code here and remove the warning
#warning "Code missing in function <LB::AttrList* LB_MovingInstrument_i::getAttributes()>"
}

void LB_MovingInstrument_i::setLevel(const char* level){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_MovingInstrument_i::setLevel(const char* level)>"
}

char* LB_MovingInstrument_i::getLevel(){
  // insert code here and remove the warning
#warning "Code missing in function <char* LB_MovingInstrument_i::getLevel()>"
}

// End of example implementational code
