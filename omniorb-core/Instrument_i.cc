//
// Example code for implementing IDL interfaces in file Instrument.idl
//

#include <iostream.h>
#include <Instrument.hh>

//
// Example class implementing IDL interface LB::Instrument
//
class LB_Instrument_i: public POA_LB::Instrument,
                public PortableServer::RefCountServantBase {
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_Instrument_i();
public:
  // standard constructor
  LB_Instrument_i();
  virtual ~LB_Instrument_i();

  // methods corresponding to defined IDL attributes and operations
  char* name();
  void setAttribute(const char* attr, const char* value);
  LB::AttrList* getAttributes();
  void setLevel(const char* level);
  char* getLevel();
  
};

//
// Example implementational code for IDL interface LB::Instrument
//
LB_Instrument_i::LB_Instrument_i(){
  // add extra constructor code here
}
LB_Instrument_i::~LB_Instrument_i(){
  // add extra destructor code here
}
//   Methods corresponding to IDL attributes and operations
char* LB_Instrument_i::name(){
  // insert code here and remove the warning
#warning "Code missing in function <char* LB_Instrument_i::name()>"
}

void LB_Instrument_i::setAttribute(const char* attr, const char* value){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_Instrument_i::setAttribute(const char* attr, const char* value)>"
}

LB::AttrList* LB_Instrument_i::getAttributes(){
  // insert code here and remove the warning
#warning "Code missing in function <LB::AttrList* LB_Instrument_i::getAttributes()>"
}

void LB_Instrument_i::setLevel(const char* level){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_Instrument_i::setLevel(const char* level)>"
}

char* LB_Instrument_i::getLevel(){
  // insert code here and remove the warning
#warning "Code missing in function <char* LB_Instrument_i::getLevel()>"
}

// End of example implementational code
