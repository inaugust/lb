#include "Fader_i.hh"
#include "lb.hh"


int initialize_faders (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing faders\n");

  LB_Fader_i* i_i = new LB_Fader_i("1");
  /* This pointer won't ever be freed */
  LB::Fader_ptr i_ref = i_i->_this();
  lb->putFader(i_ref);

  fprintf(stderr, "Done initializing faders\n");

}


LB_Fader_i::LB_Fader_i(const char *name)
{
  this->my_name=strdup(name);
  this->level=0;
  pthread_mutex_init (&this->thread_lock, NULL);
  pthread_mutex_init (&this->level_lock, NULL);
  this->thread_exists=0;
  this->running=0;
}

LB_Fader_i::~LB_Fader_i()
{
}

//   Methods corresponding to IDL attributes and operations
char* LB_Fader_i::name()
{
  return this->my_name;
}

extern "C"
void *bootstrap(void *object)
{
  ((LB_Fader_i *)object)->do_run();
}


void LB_Fader_i::run(double level, double time)
{

  pthread_mutex_lock(&this->thread_lock);

  this->fromlevel=this->level;
  this->tolevel=level;
  this->intime=time;

  if (this->thread_exists)
    {
      this->running=0;
      pthread_mutex_unlock(&this->thread_lock);
      pthread_join (this->my_thread, NULL);
      pthread_mutex_lock(&this->thread_lock);
    }
  else
    {
      this->running=1;
      this->thread_exists=1;
      pthread_create(&this->my_thread, (pthread_attr_t *)NULL,
		     bootstrap,
		     this);
    }
  pthread_mutex_unlock(&this->thread_lock);
}


double my_time(void)
{
  struct timeval tv;
  gettimeofday(&tv, NULL);
  
  double r = tv.tv_sec + tv.tv_usec/1000000.0;
  return r;
}

void LB_Fader_i::do_run(void)
{
  printf ("%s from %f to %f scheduled for %f\n", this->my_name, this->fromlevel, this->tolevel, this->intime);
  
  double start = my_time();

  double level=this->fromlevel;
  double fromlevel=this->fromlevel;
  double tolevel=this->tolevel;
  double intime=this->intime;

  if (tolevel-fromlevel==0)
    {
      printf ("nothing to do, levels are the same\n");
      pthread_mutex_lock(&this->thread_lock);
      this->thread_exists=0;
      pthread_mutex_unlock(&this->thread_lock);
      /*
      if (self.callback):
	self.callback(self.callback_arg, self.name, None)
      */
      return;
    }
  double delta;
  if ((tolevel-fromlevel)>0)
    delta=.4;
  else
    delta=-.4;
  /*
  if (intime<=3)
    delta=delta*((long)((1/(4*exp(intime-3)))+1.5));
  */
  if (intime==0)
    {
      printf ("nothing to do, time is 0\n");
      this->setLevel(tolevel);
      pthread_mutex_lock(&this->thread_lock);
      this->thread_exists=0;
      pthread_mutex_unlock(&this->thread_lock);
      /*
      if (self.callback):
	self.callback(self.callback_arg, self.name, None)
      */
      return;
    }
  double adelta=fabs(delta);
  long steps=long(fabs(tolevel-fromlevel)/adelta);

  double endtime=start+intime;
  double delay=intime/steps;
  double *times = (double *) malloc (sizeof(double)*steps);
  double *levels = (double *) malloc (sizeof(double)*steps);

  printf ("schedule\n");
  double mylevel=level;
  double mytime=start;
  for (long s=0; s<steps; s++)
    {
      mylevel=mylevel+delta;
      mytime=mytime+delay;
      //print str(mylevel) + ' @ ' + str(mytime)
      times[s]=mytime;
      levels[s]=mylevel;
    }
  printf ("running\n");

  long t;
  for (long s=0; s<steps; s++)
    {
      //#print str(target_level) + ' @ ' + str(target_time) + ' s ' + 
      //str(max(times[s]-my_time(),0))

      t = long((times[s]-my_time())*1000000);
      if (t>0)
	usleep (t);
      //printf ("%li @ %f s %li\n", levels[s], times[s], t);
      this->setLevel(levels[s]);
    }           
  double end=my_time();
  printf ("%s from %f to %f in %f\n", this->my_name, fromlevel, tolevel, end-start);
  pthread_mutex_lock(&this->thread_lock);
  this->thread_exists=0;
  pthread_mutex_unlock(&this->thread_lock);
  /*
    if (self.callback):
    self.callback(self.callback_arg, self.name, None)
  */
}


void LB_Fader_i::act_on_set_ratio (double ratio)
{
  printf ("Fader ratio %li\n", ratio);
}

void LB_Fader_i::stop()
{
  /*
        self.threadlock.acquire()
        if (self.mythread):
            self.running=0
            self.threadlock.release()
            self.mythread.join()
            return
        self.threadlock.release()
*/
}

void LB_Fader_i::setLevel(double level)
{
  pthread_mutex_lock(&this->level_lock);

  this->act_on_set_ratio (level);
                
  /*
    if (self.callback):
    self.callback(self.callback_arg, self.name, self.matrix)
  */

  pthread_mutex_unlock(&this->level_lock);
}

CORBA::Boolean LB_Fader_i::isRunning()
{
  /*
        self.threadlock.acquire()
        if (self.mythread):
            ret=1
        else:
            ret=0
        self.threadlock.release()
        return ret
  */
}
