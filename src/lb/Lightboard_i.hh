#ifndef _LIGHTBOARD_I_HH_
#define _LIGHTBOARD_I_HH_

#include "Dimmer_i.hh"
#include "Instrument_i.hh"
#include "CrossFader_i.hh"
#include "LevelFader_i.hh"
#include "CueFader_i.hh"
#include "lb.hh"

#include "Lightboard.hh"

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

  pthread_t event_thread;
  pthread_mutex_t queue_lock;
  GSList *event_queue_head;
  GSList *event_queue_tail;

  GHashTable *drivers;

  char *my_name;

public:
  // standard constructor
  LB_Lightboard_i(const char *name);
  virtual ~LB_Lightboard_i();

  // methods corresponding to defined IDL attributes and operations
  char* name();
  CORBA::ULong dimmerRange();
  LB::Instrument_ptr getInstrument(const char* name);
  void putInstrument(LB::Instrument_ptr ins);

  LB::Fader_ptr getFader(const char* name);
  void putFader(LB::Fader_ptr fadr);

  LB::Dimmer_ptr getDimmer(const char* name);
  void putDimmer(LB::Dimmer_ptr dimr);

  CORBA::Long createInstrument(const char* show, const char* name, 
			       CORBA::Long dimmer_start);
  
  CORBA::Long createInstrument(const char* show, const char* name, 
			       const char* driver, 
			       const LB::ArgList& arguments);

  CORBA::Long createLevelFader(const char* show, const char* name);
  CORBA::Long createCueFader(const char* show, const char* name);
  CORBA::Long createCrossFader(const char* show, const char* name);

 
  /* This function is not public.  I mean it.  Don't call it! */
  void addEvent(const LB::Event& evt);
  void addDriver(const char* name, LB::InstrumentFactory_ptr fact);

  void do_run_events();
  void print_queue();
};

#endif _LIGHTBOARD_I_HH_
