#ifndef __FADER_I_HH__
#define __FADER_I_HH__

#include "lb.hh"

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <math.h>
#include <unistd.h>
#include <glib.h>


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

  pthread_t my_thread;
  int thread_exists;
  int running;
  pthread_mutex_t thread_lock;
  pthread_mutex_t level_lock;

  void stopped();  // emit stopped event
  void completed();  // emit completed event

protected:
  char *my_name;
  virtual void act_on_set_ratio (double ratio);
  double fromlevel;
  double tolevel;
  double intime;
  double level;

  /* The fader will choose a number of steps so that: There are no
     more steps than are needed so that each one has at least the
     minimum percent change.  And there are no more steps than the
     maximum refresh rate permits.
  */

  double minimum_percent_change;
  double maximum_refresh_rate;

  GSList *level_listeners;
  GSList *run_listeners;  
  GSList *stop_listeners;  
  GSList *complete_listeners;  
  GSList *source_listeners;  

  pthread_mutex_t listener_lock;
  CORBA::Long listener_id;

  CORBA::Long addListener(GSList **list, const LB::EventListener_ptr l);
  void removeListener(GSList **list, const CORBA::Long id);
  
public:
  // standard constructor
  LB_Fader_i(const char *name);
  virtual ~LB_Fader_i();

  // methods corresponding to defined IDL attributes and operations
  char* name();
  void run(double level, double time);
  void stop();
  void setLevel(double level);
  void setLevel_withTime(double level, double time_left);  // not CORBA
  CORBA::Double getLevel();
  CORBA::Boolean isRunning();
  CORBA::Long addRunListener(const LB::EventListener_ptr l);
  void removeRunListener(CORBA::Long);
  CORBA::Long addStopListener(const LB::EventListener_ptr l);
  void removeStopListener(CORBA::Long);
  CORBA::Long addLevelListener(const LB::EventListener_ptr l);
  void removeLevelListener(CORBA::Long);
  CORBA::Long addCompleteListener(const LB::EventListener_ptr l);
  void removeCompleteListener(CORBA::Long);
  CORBA::Long addSourceListener(const LB::EventListener_ptr l);
  void removeSourceListener(CORBA::Long);
  

  /* This function is not public.  I mean it.  Don't call it! */
  void do_run ();

  void sendEvent(const LB::Event& evt);
};
#endif __FADER_I_HH__
