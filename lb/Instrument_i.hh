#ifndef __INSTRUMENT_I_HH__
#define __INSTRUMENT_I_HH__

#include "lb.hh"

#include <glib.h>
#include <stdio.h>
#include <stdlib.h>

int initialize_instruments(LB::Lightboard_ptr lb);


class LB_Instrument_i : public POA_LB::Instrument,
                        public PortableServer::RefCountServantBase
{
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
  GSList *gobo_rpm_listeners;

  pthread_mutex_t listener_lock;
  CORBA::Long listener_id;


  pthread_mutex_t source_lock;

  GHashTable *sources;
  virtual void updateLevelFromSources();

  CORBA::Long addListener(GSList **list, const LB::EventListener_ptr l);
  void removeListener(GSList **list, CORBA::Long id);


public:
  // standard constructor
  LB_Instrument_i(const char *name, int dimmer_start);
  virtual ~LB_Instrument_i();

  // methods corresponding to defined IDL attributes and operations
  char *name();
  LB::AttrList *getAttributes();

  virtual void setLevelFromSource(CORBA::Double level, const char *source);

  virtual void setLevel(CORBA::Double level);
  virtual CORBA::Double getLevel();
  CORBA::Long addLevelListener(const LB::EventListener_ptr l);
  void removeLevelListener(CORBA::Long id);

  virtual void setTarget(CORBA::Double x, CORBA::Double y, CORBA::Double z);
  virtual void getTarget(CORBA::Double& x,
                         CORBA::Double& y,
                         CORBA::Double& z);
  CORBA::Long addTargetListener(const LB::EventListener_ptr l);
  void removeTargetListener(CORBA::Long id);

  virtual void setGoboRPM(CORBA::Double rpm);
  virtual void getGoboRPM(CORBA::Double& rpm);
  CORBA::Long addGoboRPMListener(const LB::EventListener_ptr l);
  void removeGoboRPMListener(CORBA::Long id);

  void sendEvent(const LB::Event& evt);
};


class LB_InstrumentFactory_i : public POA_LB::InstrumentFactory,
                               public PortableServer::RefCountServantBase
{
protected:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_InstrumentFactory_i();
public:
  // standard constructor
  LB_InstrumentFactory_i();
  virtual ~LB_InstrumentFactory_i();

  LB::Instrument_ptr createInstrument(const char *name,
                                      const LB::ArgList& arguments);
};

#endif
