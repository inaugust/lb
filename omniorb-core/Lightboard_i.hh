#ifndef _LIGHTBOARD_I_HH_
#define _LIGHTBOARD_I_HH_

#include "Dimmer_i.hh"
#include "lb.hh"

#include <Lightboard.hh>

//
// Example class implementing IDL interface LB::Lightboard
//
class LB_Lightboard_i: public POA_LB::Lightboard,
                public PortableServer::RefCountServantBase {
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_Lightboard_i();

  map <const char *, LB::Dimmer_ptr, ltstr> dimmers;
  map <const char *, LB::Instrument_ptr, ltstr> instruments;
  map <const char *, LB::Fader_ptr, ltstr> faders;

public:
  // standard constructor
  LB_Lightboard_i();
  virtual ~LB_Lightboard_i();

  // methods corresponding to defined IDL attributes and operations
  CORBA::ULong dimmerRange();
  LB::Instrument_ptr getInstrument(const char* name);
  void putInstrument(LB::Instrument_ptr ins);

  LB::Fader_ptr getFader(const char* name);
  void putFader(LB::Fader_ptr fadr);

  LB::Dimmer_ptr getDimmer(const char* name);
  void putDimmer(LB::Dimmer_ptr dimr);
};

#endif _LIGHTBOARD_I_HH_