#ifndef __LEVELFADER_I_HH__
#define __LEVELFADER_I_HH__

#include <iostream.h>
#include "LevelFader.hh"
#include "Fader_i.hh"

#include "Lightboard.hh"
#include "lb.hh"

int initialize_levelfaders (LB::Lightboard_ptr lb);

class LB_LevelFader_i: public POA_LB::LevelFader,
		       //public PortableServer::RefCountServantBase 
		       public LB_Fader_i
{
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_LevelFader_i();

  LB::Cue *cue;
  LB::Instrument_ptr *instruments;

protected:
  void act_on_set_ratio (double ratio);

public:
  // standard constructor
  LB_LevelFader_i(const char *name);
  virtual ~LB_LevelFader_i();

  // methods corresponding to defined IDL attributes and operations
  void setCue(const LB::Cue& incue);
  void clear();

  /*
  char* name();
  void run(CORBA::Double level, CORBA::Double time);
  void stop();
  void setLevel(CORBA::Double level);
  CORBA::Boolean isRunning();
  */  
};

#endif __LEVELFADER_I_HH__
