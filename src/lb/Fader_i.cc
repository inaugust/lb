#include "Fader_i.hh"

int initialize_faders (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing faders\n");
  fprintf(stderr, "Done initializing faders\n");
}

LB_Fader_i::LB_Fader_i(const char *name)
{
  this->minimum_percent_change = 100.0/255.0;  // About 0.39 % per step
  this->maximum_refresh_rate = 30.0; // 30 updates per second

  this->my_name=strdup(name);
  this->level=0.0;
  pthread_mutex_init (&this->thread_lock, NULL);
  pthread_mutex_init (&this->level_lock, NULL);
  pthread_mutex_init (&this->listener_lock, NULL);
  pthread_mutex_init (&this->load_lock, NULL);
  this->thread_exists=0;
  this->running=0;

  level_listeners = NULL;
  run_listeners = NULL;
  stop_listeners = NULL;
  complete_listeners = NULL;
  source_listeners = NULL;
  listener_id = 0;
}

LB_Fader_i::~LB_Fader_i()
{
}

//   Methods corresponding to IDL attributes and operations
char* LB_Fader_i::name()
{
  CORBA::String_var ret;

  ret=CORBA::string_dup(this->my_name);
  return ret._retn();
}

extern "C"
{
  static void *bootstrap(void *object)
  {
    ((LB_Fader_i *)object)->do_run();
  }
}

void LB_Fader_i::run(double level, double time)
{

  pthread_mutex_lock(&this->thread_lock);

  this->fromlevel=this->level;
  this->tolevel=level;
  this->intime=time;

  if (this->thread_exists)
    {
      pthread_mutex_unlock(&this->thread_lock);
      this->stop();
      pthread_mutex_lock(&this->thread_lock);
    }

  this->running=1;
  this->thread_exists=1;
  pthread_create(&this->my_thread, (pthread_attr_t *)NULL,
		 bootstrap,
		 this);

  pthread_mutex_unlock(&this->thread_lock);

  if (this->run_listeners)
    {
      LB::Event evt;

      evt.source=this->_this();
      evt.value.length(2);
      evt.value[0]=level;
      evt.value[1]=time;
      evt.type=LB::event_fader_run;

      lb->addEvent(evt);
    }
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
  printf ("do_run locka\n");
  pthread_mutex_lock(&this->load_lock);
  printf ("do_run lockb\n");

  printf ("%s from %f to %f scheduled for %f\n", this->my_name, this->fromlevel, this->tolevel, this->intime);
  
  double start = my_time();

  double level=this->fromlevel;
  double fromlevel=this->fromlevel;
  double tolevel=this->tolevel;
  double intime=this->intime;

  if (tolevel-fromlevel==0)
    {
      printf ("nothing to do, levels are the same\n");
      printf ("do_run unlock\n");
      pthread_mutex_unlock(&this->load_lock);
      pthread_mutex_lock(&this->thread_lock);
      this->thread_exists=0;
      pthread_mutex_unlock(&this->thread_lock);
      this->running=0;
      this->completed();

      return;
    }
  double delta;
  if ((tolevel-fromlevel)>0)
    delta=minimum_percent_change;
  else
    delta=-minimum_percent_change;

  /*
  if (intime<=3)
    delta=delta*((long)((1/(4*exp(intime-3)))+1.5));
  */
  if (intime==0)
    {
      printf ("nothing to do, time is 0\n");
      printf ("do_run unlock\n");
      pthread_mutex_unlock(&this->load_lock);
      this->setLevel(tolevel);
      pthread_mutex_lock(&this->thread_lock);
      this->thread_exists=0;
      pthread_mutex_unlock(&this->thread_lock);
      this->running=0;
      this->completed();
      return;
    }
  double adelta=fabs(delta);
  long steps=(long)(fabs(tolevel-fromlevel)/adelta);

  printf ("delta1, adelta1: %f %f\n", delta,adelta);
  printf ("steps1         : %li\n", steps);

  if(float(steps)/intime > maximum_refresh_rate)
    {
      steps = long(maximum_refresh_rate * intime);
      delta = (tolevel-fromlevel)/steps;
      adelta=fabs(delta);
    }

  printf ("delta2, adelta2: %f %f\n", delta,adelta);
  printf ("steps 2      : %li\n", steps);
  
  // Correct for rounding errors.

  if ((tolevel-fromlevel)>0)
    while ((double(steps) * delta) < (tolevel-fromlevel)) steps++;
  else
    while ((double(steps) * delta) > (tolevel-fromlevel)) steps++;

  printf ("steps 3      : %li\n", steps);
  /*
  printf ("steps: ((%f - %f)=%f)/%f = %f =? %li\n", tolevel, fromlevel,
	  fabs(tolevel-fromlevel), adelta, fabs(tolevel-fromlevel)/adelta, 
	  steps);
  */

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
      // printf ("%li: %f @ %f\n", s, mylevel, mytime);
      times[s]=mytime;
      levels[s]=mylevel;
    }
  printf ("running\n");

  long t;
  double left, mt;
  for (long s=0; s<steps; s++)
    {
      if (!running) break;
      //#print str(target_level) + ' @ ' + str(target_time) + ' s ' + 
      //str(max(times[s]-my_time(),0))

      mt = my_time();
      left = times[steps-1]-mt;
      t = long((times[s]-mt)*1000000);
      if (t>0)
	usleep (t);
      //printf ("%li @ %f s %li\n", levels[s], times[s], t);
      this->setLevel_withTime(levels[s], left);
    }           
  double end=my_time();
  printf ("%s from %f to %f in %f\n", this->my_name, fromlevel, tolevel, end-start);
  pthread_mutex_lock(&this->thread_lock);
  this->thread_exists=0;
  pthread_mutex_unlock(&this->thread_lock);

  free (times);
  free (levels);

  if (running)
    {
      this->running=0;
      this->completed();
    }
  
  /*
    if (self.callback):
    self.callback(self.callback_arg, self.name, None)
  */

  printf ("do_run unlock\n");
  pthread_mutex_unlock(&this->load_lock);
}


void LB_Fader_i::act_on_set_ratio (double ratio)
{
  printf ("Fader ratio %li\n", ratio);
}

void LB_Fader_i::stopped()
{
  this->intime=0.0;

  if (this->stop_listeners)
    {
      LB::Event evt;
      
      evt.source=this->_this();
      evt.value.length(0);
      evt.type=LB::event_fader_stop;
      
      lb->addEvent(evt);
    }

  pthread_mutex_unlock(&this->thread_lock);
}

void LB_Fader_i::completed()
{
  this->intime=0.0;
  if (this->complete_listeners)
    {
      LB::Event evt;
      
      evt.source=this->_this();
      evt.value.length(0);
      evt.type=LB::event_fader_complete;
      
      lb->addEvent(evt);
    }
}

void LB_Fader_i::stop()
{
  pthread_mutex_lock(&this->thread_lock);

  if (this->thread_exists)
    {
      this->running=0;
      pthread_mutex_unlock(&this->thread_lock);
      pthread_join (this->my_thread, NULL);

      this->stopped();

      return;
    }

  pthread_mutex_unlock(&this->thread_lock);

}

/* I don't want to overload the CORBA functions.  That could be
   confusing.  This function is to be called only from the fader
   run routine. */
void LB_Fader_i::setLevel_withTime(double level, double time_left)
{
  pthread_mutex_lock(&this->level_lock);

  this->level=level;
  this->act_on_set_ratio (level/100.0);
  if (this->level_listeners)
    {
      LB::Event evt;

      evt.source=this->_this();
      evt.value.length(2);
      evt.value[0]=level;
      evt.value[1]=time_left;

      evt.type=LB::event_fader_level;

      lb->addEvent(evt);
    }

  pthread_mutex_unlock(&this->level_lock);
}

void LB_Fader_i::setLevel(double level)
{
  printf ("Fader level %f\n", level);
  printf ("setlevel locka\n");
  pthread_mutex_lock(&this->load_lock);
  printf ("setlevel lockb\n");
  pthread_mutex_lock(&this->level_lock);

  this->level=level;
  this->act_on_set_ratio (level/100.0);
  if (this->level_listeners)
    {
      LB::Event evt;

      evt.source=this->_this();
      evt.value.length(1);
      evt.value[0]=level;
      evt.type=LB::event_fader_level;

      lb->addEvent(evt);
    }

  pthread_mutex_unlock(&this->level_lock);
  printf ("setlevel unlock\n");
  pthread_mutex_unlock(&this->load_lock);
}

CORBA::Double LB_Fader_i::getLevel()
{
  return this->level;
}

CORBA::Boolean LB_Fader_i::isRunning()
{
  return running;
}


void LB_Fader_i::sendEvent(const LB::Event &evt)
{
  pthread_mutex_lock(&this->listener_lock);
  GSList *list, **handle;
  switch (evt.type)
    {
    case LB::event_fader_level:    handle = &this->level_listeners;    break;
    case LB::event_fader_run:      handle = &this->run_listeners;      break;
    case LB::event_fader_stop:     handle = &this->stop_listeners;     break;
    case LB::event_fader_complete: handle = &this->complete_listeners; break;
    case LB::event_fader_source:   handle = &this->source_listeners;   break;
    }
  list = *handle;
  GSList *to_remove = NULL;
  while (list)
    {
      ListenerRecord *r = (ListenerRecord *) list->data;
      try
	{
	  r->listener->receiveEvent(evt);
	}
      catch (...)
	{
	  to_remove = g_slist_append(to_remove, r);
	}
      list=list->next;
    }
  if (to_remove)
    {
      while (to_remove)
	{
	  ListenerRecord *r = (ListenerRecord *) to_remove->data;
	  *handle=g_slist_remove(*handle, to_remove->data);
	  to_remove=to_remove->next;
	  delete r;
	}
      g_slist_free(to_remove);
    }
  pthread_mutex_unlock(&this->listener_lock);
}

CORBA::Long LB_Fader_i::addListener(GSList **list,
				    const LB::EventListener_ptr l)
{
  ListenerRecord *r = new ListenerRecord;

  pthread_mutex_lock(&this->listener_lock);

  r->id = this->listener_id++;
  r->listener = LB::EventListener::_duplicate(l);
  *list=g_slist_append(*list, r);

  pthread_mutex_unlock(&this->listener_lock);
  return r->id;
}

void LB_Fader_i::removeListener(GSList **list,
				CORBA::Long id)
{
  ListenerRecord *r;
  GSList *l = *list;

  pthread_mutex_lock(&this->listener_lock);

  while (l)
    {
      r = (ListenerRecord *)l->data;
      if (r->id == id)
	{
	  *list = g_slist_remove(*list, r);
	  delete r;
	  break;
	}
      l=l->next;
    }
  
  pthread_mutex_unlock(&this->listener_lock);
}

CORBA::Long LB_Fader_i::addLevelListener(const LB::EventListener_ptr l)
{
  return this->addListener(&this->level_listeners, l);
}

void LB_Fader_i::removeLevelListener(CORBA::Long id)
{
  this->removeListener(&this->level_listeners, id);
}

/////////

CORBA::Long LB_Fader_i::addRunListener(const LB::EventListener_ptr l)
{
  return this->addListener(&this->run_listeners, l);
}

void LB_Fader_i::removeRunListener(CORBA::Long id)
{
  this->removeListener(&this->run_listeners, id);
}

/////////

CORBA::Long LB_Fader_i::addStopListener(const LB::EventListener_ptr l)
{
  return this->addListener(&this->stop_listeners, l);
}

void LB_Fader_i::removeStopListener(CORBA::Long id)
{
  this->removeListener(&this->stop_listeners, id);
}

/////////

CORBA::Long LB_Fader_i::addCompleteListener(const LB::EventListener_ptr l)
{
  return this->addListener(&this->complete_listeners, l);
}

void LB_Fader_i::removeCompleteListener(CORBA::Long id)
{
  this->removeListener(&this->complete_listeners, id);
}


///////////


CORBA::Long LB_Fader_i::addSourceListener(const LB::EventListener_ptr l)
{
  return this->addListener(&this->source_listeners, l);
}

void LB_Fader_i::removeSourceListener(CORBA::Long id)
{
  this->removeListener(&this->source_listeners, id);
}
