#ifndef __INSTRUMENT_I_HH__
#define __INSTRUMENT_I_HH__

#include "Instrument.hh"
#include "Lightboard.hh"

#include <glib.h>

int initialize_instruments (LB::Lightboard_ptr lb);

class LB_Instrument_i: public POA_LB::Instrument,
                public PortableServer::RefCountServantBase {
protected:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_Instrument_i();

  char *my_name;
  CORBA::Double my_level;

  int dimmer_start;

  LB::Dimmer_ptr level_dimmer;
  
  GSList *level_listeners;
  GSList *target_listeners;

  pthread_mutex_t listener_lock;

  virtual void fireLevelEvent(const LB::Event &evt);
  virtual void fireTargetEvent(const LB::Event &evt);

public:
  // standard constructor
  LB_Instrument_i(const char *name, int dimmer_start);
  virtual ~LB_Instrument_i();

  // methods corresponding to defined IDL attributes and operations
  char* name();
  LB::AttrList* getAttributes();

  virtual void setLevel(CORBA::Double level);
  virtual CORBA::Double getLevel();
  
  void addLevelListener(const char *l);
  void removeLevelListener(const char *l);

  virtual void setTarget(CORBA::Double x, CORBA::Double y, CORBA::Double z);
  virtual void getTarget(CORBA::Double& x, CORBA::Double& y, CORBA::Double& z);

  void addTargetListener(const char *l);
  void removeTargetListener(const char *l);
};

#endif __INSTRUMENT_I_HH__
