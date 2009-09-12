#ifndef __CROSSFADER_I_HH__
#define __CROSSFADER_I_HH__

#include "Fader_i.hh"

int initialize_crossfaders(LB::Lightboard_ptr lb);


class LB_CrossFader_i : public POA_LB::CrossFader,
//                public PortableServer::RefCountServantBase
                        public LB_Fader_i
{
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_CrossFader_i();

  LB::Cue up_cue;
  LB::Cue down_cue;

  LB::Instrument_ptr *instruments;

  double up_time;
  double down_time;

  void act_on_set_ratio(double ratio);


public:
  // standard constructor
  LB_CrossFader_i(const char *name);
  virtual ~LB_CrossFader_i();

  // methods corresponding to defined IDL attributes and operations
  void setCues(const LB::Cue& downcue, const LB::Cue& upcue);

  void setTimes(CORBA::Double downtime, CORBA::Double uptime);

  char *getUpCueName();
  char *getDownCueName();

  CORBA::Double getUpCueTime();
  CORBA::Double getDownCueTime();

  void clear();


  /*
   *  char* name();
   *  void run(CORBA::Double level, CORBA::Double time);
   *  void stop();
   *  void setLevel(CORBA::Double level);
   *  CORBA::Boolean isRunning();
   */
};

#endif
