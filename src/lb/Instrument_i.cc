//
// Example code for implementing IDL interfaces in file Instrument.idl
//

#include <string>

#include "lb.hh"
#include "Instrument_i.hh"


int initialize_instruments (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing instruments\n");

  LB_InstrumentFactory_i* i_i = new LB_InstrumentFactory_i();
  /* This pointer won't ever be freed */
  LB::InstrumentFactory_ptr i_ref = i_i->_this();
  lb->addDriver("instrument", i_ref);
  
  fprintf(stderr, "Done initializing instruments\n");
}

LB_Instrument_i::LB_Instrument_i(const char *name, int dimmer_start)
{
  char dname[32];
  this->my_name=strdup(name);
  this->my_level=0L;
 
  this->dimmer_start=dimmer_start;
  sprintf (dname, "%i", dimmer_start);

  CORBA::Object_var obj;
  CosNaming::Name cname;
  cname.length(1);

  cname[0].id   = (const char *)dname;
  cname[0].kind   = (const char *)"Dimmer";

  obj=dimmerContext->resolve(cname);
  this->level_dimmer = LB::Dimmer::_narrow(obj);

  pthread_mutex_init (&this->listener_lock, NULL);
  pthread_mutex_init (&this->source_lock, NULL);

  this->level_listeners=NULL;
  this->target_listeners=NULL;
  this->gobo_rpm_listeners=NULL;
  this->sources=g_hash_table_new (g_str_hash, g_str_equal);
  
  /*
  printf ("Instrument %s, at %i, dimmer %p\n", this->my_name, 
	  this->dimmer_start,
	  this->level_dimmer);
  */
}

LB_Instrument_i::~LB_Instrument_i()
{
}

char* LB_Instrument_i::name()
{
  CORBA::String_var ret;

  ret=CORBA::string_dup(this->my_name);
  return ret._retn();
}

LB::AttrList* LB_Instrument_i::getAttributes()
{
  LB::AttrList_var ret = new LB::AttrList;

  ret->length(1);
  ret[0]=LB::attr_level;
  return ret._retn();
}

void LB_Instrument_i::setLevelFromSource(CORBA::Double level, 
					 const char* source)
{
  double *v;
  char *p;

  pthread_mutex_lock(&this->source_lock);

  //printf ("%s @ %f\n", source, level);
      
  if (level)
    {
      //printf ("must insert\n");
      v=(double *)g_hash_table_lookup(this->sources, source);
      if (v)
	{
	  //printf ("found\n");
	  if (*v==level)
	    {
	      pthread_mutex_unlock(&this->source_lock);
	      return;
	    }
	  *v=level;
	}
      else
	{
	  //printf ("not found\n");
	  double *v = (double *) malloc(sizeof(double));
      
	  *v=level;
	  p = strdup (source);
	  //printf ("inserting source %p, orig %p\n", p, source);
	  g_hash_table_insert (this->sources, p, v);
	}
    }
  else
    {
      //printf ("must remove\n");
      //printf ("%s @ %f\n", source, level);
      v=(double *)g_hash_table_lookup(this->sources, source);
      //printf ("%s @ %f\n", source, level);
      if (v)
	{
	  char **okey;
	  double **oval;
	  
	  //printf ("%s @ %f\n", source, level);
	  g_hash_table_lookup_extended(this->sources, source, (void **)okey, 
				       (void **)oval);
	  //printf ("%s @ %f\n", source, level);

	  //printf ("key pointer %p\n", okey);
	  //printf ("key value %s\n", *okey);

	  //printf ("val pointer %p\n", oval);
	  //printf ("val value %f\n", *oval);

	  //printf ("orig %p\n", source);

	  g_hash_table_remove(this->sources, source);


	  free (*oval);
	  //printf ("deleted\n");
	  //printf ("%s @ %f\n", source, level);
	  free (*okey);
	  //printf ("freed\n");
	  //printf ("%s @ %f\n", source, level);
	  //printf ("%s @ %f\n", source, level);
	}
    }
  //printf ("%s @ %f\n", source, level);
  //printf (">update\n");
  this->updateLevelFromSources();
  //printf ("<update\n");
  pthread_mutex_unlock(&this->source_lock);
}

static void find_max(gpointer key, double *value, double *max)
{
  if (*value > *max)
    *max=*value;
}

void LB_Instrument_i::updateLevelFromSources()
{
  double max=0;

  g_hash_table_foreach(this->sources, find_max, &max);
  //printf ("found max %f\n", max);
  this->setLevel(max);
}

void LB_Instrument_i::setLevel(CORBA::Double level)
{
  this->my_level=level;
  this->level_dimmer->setValue((long)((level/100.0)*255.0));
  if (this->level_listeners)
    {
      LB::Event evt;

      evt.source=this->_this();
      evt.value.length(1);
      evt.value[0]=level;
      evt.type=LB::event_instrument_level;

      lb->addEvent(evt);
    }
}

CORBA::Double LB_Instrument_i::getLevel()
{
  return this->my_level;
}

void LB_Instrument_i::sendEvent(const LB::Event &evt)
{
  pthread_mutex_lock(&this->listener_lock);
  GSList *list, **handle;
  switch (evt.type)
    {
    case LB::event_instrument_level:  handle = &this->level_listeners;   break;
    case LB::event_instrument_target: handle = &this->target_listeners;  break;
    case LB::event_instrument_gobo_rpm: handle = &this->gobo_rpm_listeners;  break;
    }
  list = *handle;
  GSList *to_remove = NULL;
  while (list)
    {
      try
	{
	  ((LB::EventListener_ptr) list->data)->receiveEvent(evt);
	}
      catch (...)
	{
	  to_remove = g_slist_append(to_remove, list->data);
	}
      list=list->next;
    }
  if (to_remove)
    {
      while (to_remove)
	{
	  *handle=g_slist_remove(*handle, to_remove->data);
	  to_remove=to_remove->next;
	}
      g_slist_free(to_remove);
    }
  pthread_mutex_unlock(&this->listener_lock);
}


void LB_Instrument_i::addLevelListener(const LB::EventListener_ptr l)
{
  pthread_mutex_lock(&this->listener_lock);
  LB::EventListener_ptr p = LB::EventListener::_duplicate(l);
  this->level_listeners=g_slist_append(this->level_listeners, p);
  pthread_mutex_unlock(&this->listener_lock);
}

void LB_Instrument_i::removeLevelListener(const LB::EventListener_ptr l)
{
  pthread_mutex_lock(&this->listener_lock);
  pthread_mutex_unlock(&this->listener_lock);
}

void LB_Instrument_i::setTarget(CORBA::Double x, CORBA::Double y, CORBA::Double z)
{
}

void LB_Instrument_i::getTarget(CORBA::Double& x, CORBA::Double& y, CORBA::Double& z)
{
}

void LB_Instrument_i::addTargetListener(const LB::EventListener_ptr l)
{
  pthread_mutex_lock(&this->listener_lock);
  LB::EventListener_ptr p = LB::EventListener::_duplicate(l);
  this->target_listeners=g_slist_append(this->target_listeners, p);
  pthread_mutex_unlock(&this->listener_lock);
}

void LB_Instrument_i::removeTargetListener(const LB::EventListener_ptr l)
{
  pthread_mutex_lock(&this->listener_lock);
  pthread_mutex_unlock(&this->listener_lock);
}


void LB_Instrument_i::setGoboRPM(CORBA::Double rpm)
{
}

void LB_Instrument_i::getGoboRPM(CORBA::Double& rpm)
{
}

void LB_Instrument_i::addGoboRPMListener(const LB::EventListener_ptr l)
{
  pthread_mutex_lock(&this->listener_lock);
  LB::EventListener_ptr p = LB::EventListener::_duplicate(l);
  this->gobo_rpm_listeners=g_slist_append(this->gobo_rpm_listeners, p);
  pthread_mutex_unlock(&this->listener_lock);
}

void LB_Instrument_i::removeGoboRPMListener(const LB::EventListener_ptr l)
{
  pthread_mutex_lock(&this->listener_lock);
  pthread_mutex_unlock(&this->listener_lock);
}


/********** Factory stuff **********/

LB_InstrumentFactory_i::LB_InstrumentFactory_i()
{
}

LB_InstrumentFactory_i::~LB_InstrumentFactory_i()
{
}

LB::Instrument_ptr LB_InstrumentFactory_i::createInstrument(const char* name, 
							    const LB::ArgList& arguments)
{
  int dnum=0;

  for (int a=0; a<arguments.length(); a++)
    {
      if (strcmp(arguments[a].name, "dimmer") == 0)
	dnum = atoi(arguments[a].value);
    }

  LB_Instrument_i* i_i = new LB_Instrument_i(name, dnum);

  /* This pointer won't ever be freed */
  LB::Instrument_ptr i_ref = i_i->_this();
  return i_ref;
}
