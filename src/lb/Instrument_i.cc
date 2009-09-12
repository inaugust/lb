#include "Instrument_i.hh"

int initialize_instruments(LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing instruments\n");

  LB::StringList sl;
  sl.length(1);
  sl[0]= CORBA::string_dup("dimmer");

  LB_InstrumentFactory_i *i_i= new LB_InstrumentFactory_i();
  /* This pointer won't ever be freed */
  LB::InstrumentFactory_ptr i_ref= i_i->_this();
  lb->addDriver("instrument", sl, i_ref);

  fprintf(stderr, "Done initializing instruments\n");
} // initialize_instruments


LB_Instrument_i::LB_Instrument_i(const char *name, int dimmer_start)
{
  char dname[32];

  this->my_name= strdup(name);
  this->my_level= 0L;

  this->dimmer_start= dimmer_start;
  sprintf(dname, "%i", dimmer_start);

  CORBA::Object_var obj;
  CosNaming::Name cname;
  cname.length(1);

  cname[0].id= (const char *)dname;
  cname[0].kind= (const char *)"Dimmer";

  obj= dimmerContext->resolve(cname);
  this->level_dimmer= LB::Dimmer::_narrow(obj);

  pthread_mutex_init(&this->listener_lock, NULL);
  pthread_mutex_init(&this->source_lock, NULL);

  this->level_listeners= NULL;
  this->target_listeners= NULL;
  this->gobo_rpm_listeners= NULL;
  this->listener_id= 0;
  this->sources= g_hash_table_new(g_str_hash, g_str_equal);
}


LB_Instrument_i::~LB_Instrument_i()
{}


char *LB_Instrument_i::name()
{
  CORBA::String_var ret;

  ret= CORBA::string_dup(this->my_name);
  return ret._retn();
} // name


LB::AttrList *LB_Instrument_i::getAttributes()
{
  LB::AttrList_var ret= new LB::AttrList;

  ret->length(1);
  ret[0]= LB::attr_level;
  return ret._retn();
} // getAttributes


void LB_Instrument_i::setLevelFromSource(CORBA::Double level,
                                         const char *source)
{
  double *v;
  char   *p;

  pthread_mutex_lock(&this->source_lock);

  if (level)
  {
    v= (double *)g_hash_table_lookup(this->sources, source);
    if (v)
    {
      if (*v == level)
      {
        pthread_mutex_unlock(&this->source_lock);
        return;
      }
      *v= level;
    }
    else
    {
      double *v= (double *)malloc(sizeof(double));

      *v= level;
      p= strdup(source);
      g_hash_table_insert(this->sources, p, v);
    }
  }
  else
  {
    v= (double *)g_hash_table_lookup(this->sources, source);
    if (v)
    {
      char **okey;
      double **oval;

      g_hash_table_lookup_extended(this->sources, source, (void **)okey,
                                   (void **)oval);
      g_hash_table_remove(this->sources, source);
      free(*oval);
      free(*okey);
    }
  }
  this->updateLevelFromSources();
  pthread_mutex_unlock(&this->source_lock);
} // setLevelFromSource


static void find_max(gpointer key, double *value, double *max)
{
  if (*value > *max)
    *max= *value;
}


void LB_Instrument_i::updateLevelFromSources()
{
  double max= 0;

  g_hash_table_foreach(this->sources, (void(*) (void *,
                                                void *,
                                                void *))find_max, &max);
  this->setLevel(max);
} // updateLevelFromSources


void LB_Instrument_i::setLevel(CORBA::Double level)
{
  this->my_level= level;
  this->level_dimmer->setValue((long)((level / 100.0) * 255.0));
  if (this->level_listeners)
  {
    LB::Event evt;

    evt.source= this->_this();
    evt.value.length(1);
    evt.value[0]= level;
    evt.type= LB::event_instrument_level;

    lb->addEvent(evt);
  }
} // setLevel


CORBA::Double LB_Instrument_i::getLevel()
{
  return this->my_level;
}


void LB_Instrument_i::sendEvent(const LB::Event& evt)
{
  pthread_mutex_lock(&this->listener_lock);
  GSList *list, **handle;

  switch (evt.type)
  {
  case LB::event_instrument_level:
    handle= &this->level_listeners;
    break;

  case LB::event_instrument_target:
    handle= &this->target_listeners;
    break;

  case LB::event_instrument_gobo_rpm:
    handle= &this->gobo_rpm_listeners;
    break;
  } // switch

  list= *handle;
  GSList *to_remove= NULL;
  while (list)
  {
    ListenerRecord *r= (ListenerRecord *)list->data;
    try
    {
      r->listener->receiveEvent(evt);
    }
    catch (...)
    {
      to_remove= g_slist_append(to_remove, r);
    }
    list= list->next;
  }
  if (to_remove)
  {
    while (to_remove)
    {
      ListenerRecord *r= (ListenerRecord *)to_remove->data;
      *handle= g_slist_remove(*handle, to_remove->data);
      to_remove= to_remove->next;
      delete r;
    }
    g_slist_free(to_remove);
  }
  pthread_mutex_unlock(&this->listener_lock);
} // sendEvent


CORBA::Long LB_Instrument_i::addListener(GSList **list,
                                         const LB::EventListener_ptr l)
{
  ListenerRecord *r= new ListenerRecord;

  pthread_mutex_lock(&this->listener_lock);

  r->id= this->listener_id++;
  r->listener= LB::EventListener::_duplicate(l);
  *list= g_slist_append(*list, r);

  pthread_mutex_unlock(&this->listener_lock);
  return r->id;
} // addListener


void LB_Instrument_i::removeListener(GSList **list, CORBA::Long id)
{
  ListenerRecord *r;
  GSList *l= *list;

  pthread_mutex_lock(&this->listener_lock);

  while (l)
  {
    r= (ListenerRecord *)l->data;
    if (r->id == id)
    {
      *list= g_slist_remove(*list, r);
      break;
      delete r;
    }
    l= l->next;
  }

  pthread_mutex_unlock(&this->listener_lock);
} // removeListener


CORBA::Long LB_Instrument_i::addLevelListener(const LB::EventListener_ptr l)
{
  return this->addListener(&this->level_listeners, l);
}


void LB_Instrument_i::removeLevelListener(CORBA::Long id)
{
  this->removeListener(&this->level_listeners, id);
}


void LB_Instrument_i::setTarget(CORBA::Double x,
                                CORBA::Double y,
                                CORBA::Double z)
{}


void LB_Instrument_i::getTarget(CORBA::Double& x,
                                CORBA::Double& y,
                                CORBA::Double& z)
{}


CORBA::Long LB_Instrument_i::addTargetListener(
  const LB::EventListener_ptr l)
{
  return this->addListener(&this->target_listeners, l);
}


void LB_Instrument_i::removeTargetListener(CORBA::Long id)
{
  this->removeListener(&this->target_listeners, id);
}


void LB_Instrument_i::setGoboRPM(CORBA::Double rpm)
{}


void LB_Instrument_i::getGoboRPM(CORBA::Double& rpm)
{}


CORBA::Long LB_Instrument_i::addGoboRPMListener(
  const LB::EventListener_ptr l)
{
  return this->addListener(&this->gobo_rpm_listeners, l);
}


void LB_Instrument_i::removeGoboRPMListener(CORBA::Long id)
{
  this->removeListener(&this->gobo_rpm_listeners, id);
}


/********** Factory stuff **********/

LB_InstrumentFactory_i::LB_InstrumentFactory_i()
{}


LB_InstrumentFactory_i::~LB_InstrumentFactory_i()
{}


LB::Instrument_ptr LB_InstrumentFactory_i::createInstrument(
  const char *name,
  const LB::ArgList& arguments)
{
  int dnum= 0;

  for (int a= 0; a < arguments.length(); a++)
  {
    if (strcmp(arguments[a].name, "dimmer") == 0)
      dnum= atoi(arguments[a].value);
  }

  LB_Instrument_i *i_i= new LB_Instrument_i(name, dnum);

  /* This pointer won't ever be freed */
  LB::Instrument_ptr i_ref= i_i->_this();
  return i_ref;
} // createInstrument
