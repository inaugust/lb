#ifndef __FADER_I_HH__
#define __FADER_I_HH__
#include <iostream.h>
#include "Fader.hh"
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <math.h>
#include <unistd.h>

#include "Lightboard.hh"

int initialize_faders (LB::Lightboard_ptr lb);

//
// Example class implementing IDL interface LB::Fader
//
class LB_Fader_i: public POA_LB::Fader,
                public PortableServer::RefCountServantBase {
  LB_Fader_i& operator= (const LB_Fader_i &);
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_Fader_i();

  char *my_name;
  int level;
  pthread_t my_thread;
  int thread_exists;
  int running;
  pthread_mutex_t thread_lock;
  pthread_mutex_t level_lock;
  double fromlevel;
  double tolevel;
  double intime;

  virtual void act_on_set_ratio (double ratio);

public:
  // standard constructor
  LB_Fader_i(const char *name);
  virtual ~LB_Fader_i();

  // methods corresponding to defined IDL attributes and operations
  char* name();
  void run(double level, double time);
  void stop();
  void setLevel(double level);
  CORBA::Boolean isRunning();

  /* This function is not public.  I mean it.  Don't call it! */
  void do_run ();
};
#endif __FADER_I_HH__
