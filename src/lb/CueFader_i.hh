#ifndef __CUEFADER_I_HH__
#define __CUEFADER_I_HH__

#include "Fader_i.hh"

int initialize_cuefaders (LB::Lightboard_ptr lb);

//
// Example class implementing IDL interface LB::CueFader
//
class LB_CueFader_i: public POA_LB::CueFader,
						//		     public PortableServer::RefCountServantBase,
		     public LB_Fader_i
{
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_CueFader_i();

  LB::Cue start_cue;
  LB::Cue end_cue;
  LB::Instrument_ptr *instruments;
  LB::AttrList attributes;

  int hasAttribute(LB::AttrType attr);

protected:
  void act_on_set_ratio (double ratio);

public:
  // standard constructor
  LB_CueFader_i(const char *name);
  virtual ~LB_CueFader_i();

  // methods corresponding to defined IDL attributes and operations
  void setCues(const LB::Cue& startcue, const LB::Cue& endcue);

  void setAttributes(const LB::AttrList& attr);
  void clear();
  /*
  char* name();
  void run(const char* level, const char* time);
  void stop();
  void setLevel(const char* level);
  CORBA::Boolean isRunning();
  */
};

#endif __CUEFADER_I_HH__
