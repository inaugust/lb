//
// Example code for implementing IDL interfaces in file Lightboard.idl
//

#include "Lightboard_i.hh"
#include <stdio.h>

//
// Example implementational code for IDL interface LB::Lightboard
//
LB_Lightboard_i::LB_Lightboard_i(){
  // add extra constructor code here
}
LB_Lightboard_i::~LB_Lightboard_i(){
  // add extra destructor code here
}
//   Methods corresponding to IDL attributes and operations
CORBA::ULong LB_Lightboard_i::dimmerRange(){
  // insert code here and remove the warning
#warning "Code missing in function <CORBA::ULong LB_Lightboard_i::dimmerRange()>
"
}

LB::Instrument_ptr LB_Lightboard_i::getInstrument(const char* name){
  // insert code here and remove the warning
#warning "Code missing in function <LB::Instrument_ptr LB_Lightboard_i::getInstr
ument(const char* name)>"
}

void LB_Lightboard_i::putInstrument(LB::Instrument_ptr ins){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_Lightboard_i::putInstrument(LB::Inst
rument_ptr ins)>"
}

LB::Fader_ptr LB_Lightboard_i::getFader(const char* name){
  // insert code here and remove the warning
#warning "Code missing in function <LB::Fader_ptr LB_Lightboard_i::getFader(cons
t char* name)>"
}

void LB_Lightboard_i::putFader(LB::Fader_ptr fadr){
  // insert code here and remove the warning
#warning "Code missing in function <void LB_Lightboard_i::putFader(LB::Fader_ptr
 fadr)>"
}

LB::Dimmer_ptr LB_Lightboard_i::getDimmer(const char* name)
{
  return LB::Dimmer::_duplicate (this->dimmers[name]);
}

void LB_Lightboard_i::putDimmer(LB::Dimmer_ptr dimr)
{
  this->dimmers[dimr->name()] = dimr;
}
