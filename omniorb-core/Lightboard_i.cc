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
CORBA::ULong LB_Lightboard_i::dimmerRange()
{
  return 255;
}

LB::Instrument_ptr LB_Lightboard_i::getInstrument(const char* name)
{
  return LB::Instrument::_duplicate (this->instruments[name]);
}

void LB_Lightboard_i::putInstrument(LB::Instrument_ptr ins)
{
  this->instruments[ins->name()] = ins;
}

LB::Fader_ptr LB_Lightboard_i::getFader(const char* name)
{
  return LB::Fader::_duplicate (this->faders[name]);
}

void LB_Lightboard_i::putFader(LB::Fader_ptr fadr)
{
  this->faders[fadr->name()] = fadr;
}

LB::Dimmer_ptr LB_Lightboard_i::getDimmer(const char* name)
{
  return LB::Dimmer::_duplicate (this->dimmers[name]);
}

void LB_Lightboard_i::putDimmer(LB::Dimmer_ptr dimr)
{
  this->dimmers[dimr->name()] = dimr;
}
