#include "Lightboard_i.hh"

extern "C"
{
static void *bootstrap(void *object)
{
  ((LB_Lightboard_i *)object)->do_run_events();
}
}

LB_Lightboard_i::LB_Lightboard_i(const char *name)
{
  this->my_name= strdup(name);

  this->drivers= g_hash_table_new(g_str_hash, g_str_equal);
  this->driver_args= g_hash_table_new(g_str_hash, g_str_equal);

  pthread_mutex_init(&this->queue_lock, NULL);

  pthread_create(&this->event_thread, (pthread_attr_t *)NULL,
                 bootstrap,
                 this);
}


LB_Lightboard_i::~LB_Lightboard_i()
{}


//   Methods corresponding to IDL attributes and operations
CORBA::ULong LB_Lightboard_i::dimmerRange()
{
  return 255;
}


char *LB_Lightboard_i::name()
{
  CORBA::String_var ret;

  ret= CORBA::string_dup(this->my_name);
  return ret._retn();
} // name


CORBA::Long LB_Lightboard_i::createInstrument(const char *show,
                                              const char *name,
                                              const char *driver,
                                              const LB::ArgList& arguments)
{
  CosNaming::Name cname;

  cname.length(1);

  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  LB::InstrumentFactory_ptr fact;

  //  printf ("Creating instrument for show: %s named: %s dimmer %li\n",
  //	  show, name, dimmer_start);

  fact= (LB::InstrumentFactory_ptr)g_hash_table_lookup(this->drivers,
                                                       driver);

  LB::Instrument_var i_ref= fact->createInstrument(name, arguments);

  try
  {
    cname[0].id= (const char *)"shows";
    obj= rootNaming->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)show;
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)"instruments";
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);
  }
  catch (...)
  {
    printf("Can't get instrument context\n");
    return 1;
  }

  cname[0].id= (const char *)name;
  cname[0].kind= (const char *)"Instrument";

  try
  {
    context->bind(cname, i_ref);
  }
  catch (CosNaming::NamingContext::AlreadyBound& ex)
  {
    context->rebind(cname, i_ref);
  }
  return 0;
} // createInstrument


CORBA::Long LB_Lightboard_i::createLevelFader(const char *show,
                                              const char *name)
{
  CosNaming::Name cname;

  cname.length(1);

  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  printf("Creating levelfader for show: %s named: %s\n",
         show, name);

  LB_Fader_i *i_i= new LB_LevelFader_i(name);
  LB::Fader_var i_ref= i_i->_this();

  try
  {
    cname[0].id= (const char *)"shows";
    obj= rootNaming->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)show;
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)"faders";
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);
  }
  catch (...)
  {
    printf("Can't get fader context\n");
    return 1;
  }

  cname[0].id= (const char *)name;
  cname[0].kind= (const char *)"Fader";

  try
  {
    context->bind(cname, i_ref);
  }
  catch (CosNaming::NamingContext::AlreadyBound& ex)
  {
    context->rebind(cname, i_ref);
  }
  printf("done\n");
  return 0;
} // createLevelFader


CORBA::Long LB_Lightboard_i::createCueFader(const char *show,
                                            const char *name)
{
  CosNaming::Name cname;

  cname.length(1);

  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  printf("Creating cuefader for show: %s named: %s\n",
         show, name);

  LB_Fader_i *i_i= new LB_CueFader_i(name);
  LB::Fader_var i_ref= i_i->_this();

  try
  {
    cname[0].id= (const char *)"shows";
    obj= rootNaming->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)show;
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)"faders";
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);
  }
  catch (...)
  {
    printf("Can't get fader context\n");
    return 1;
  }

  cname[0].id= (const char *)name;
  cname[0].kind= (const char *)"Fader";

  try
  {
    context->bind(cname, i_ref);
  }
  catch (CosNaming::NamingContext::AlreadyBound& ex)
  {
    context->rebind(cname, i_ref);
  }
  printf("done\n");
  return 0;
} // createCueFader


CORBA::Long LB_Lightboard_i::createCrossFader(const char *show,
                                              const char *name)
{
  CosNaming::Name cname;

  cname.length(1);

  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  printf("Creating crossfader for show: %s named: %s\n",
         show, name);

  LB_Fader_i *i_i= new LB_CrossFader_i(name);
  LB::Fader_var i_ref= i_i->_this();

  try
  {
    cname[0].id= (const char *)"shows";
    obj= rootNaming->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)show;
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);

    cname[0].id= (const char *)"faders";
    obj= context->resolve(cname);
    context= CosNaming::NamingContext::_narrow(obj);
  }
  catch (...)
  {
    printf("Can't get fader context\n");
    return 1;
  }

  cname[0].id= (const char *)name;
  cname[0].kind= (const char *)"Fader";

  try
  {
    context->bind(cname, i_ref);
  }
  catch (CosNaming::NamingContext::AlreadyBound& ex)
  {
    context->rebind(cname, i_ref);
  }
  printf("done\n");
  return 0;
} // createCrossFader


void LB_Lightboard_i::addDriver(const char *name,
                                const LB::StringList& arguments,
                                LB::InstrumentFactory_ptr fact)
{
  GSList *list= NULL;

  for (int i= 0; i < arguments.length(); i++)
  {
    list=
      g_slist_append(list, strdup(const_cast<char *>(arguments[0]._NP_ref())));
  }

  g_hash_table_insert(this->drivers, strdup(name), fact);
  g_hash_table_insert(this->driver_args, strdup(name), list);
} // addDriver


static void add_driver_name(gpointer key, gpointer data, gpointer handle_in)
{
  GSList **list= (GSList **)handle_in;

  *list= g_slist_append(*list, strdup((char *)key));
}


LB::StringList *LB_Lightboard_i::enumerateDrivers()
{
  LB::StringList_var sl= new LB::StringList;
  GSList **list, *n;

  *list= NULL;

  g_hash_table_foreach(this->drivers, add_driver_name, list);

  int len= g_slist_length(*list);
  sl->length(len);
  n= *list;
  int count= 0;
  while (n)
  {
    sl[count++]= CORBA::string_dup((char *)n->data);
    free(n->data);
    n= n->next;
  }
  g_slist_free(*list);
  return sl._retn();
} // enumerateDrivers


LB::StringList *LB_Lightboard_i::enumerateDriverArguments(
  const char *driver)
{
  LB::StringList_var sl= new LB::StringList;
  GSList *list= NULL, *n;

  list= (GSList *)g_hash_table_lookup(this->driver_args, driver);

  int len= g_slist_length(list);
  sl->length(len);
  n= list;
  int count= 0;
  while (n)
  {
    sl[count++]= CORBA::string_dup((char *)n->data);
    n= n->next;
  }

  return sl._retn();
} // enumerateDriverArguments


void LB_Lightboard_i::print_queue(void)
{
  printf("head: %p tail: %p\n", event_queue_head, event_queue_tail);
  int i= 0;
  GSList *l= event_queue_head;
  while (l)
  {
    printf("%i %p\n", i, l);
    l= l->next;
    i++;
  }
  printf("end of queue\n");
} // print_queue


void LB_Lightboard_i::addEvent(const LB::Event& evt)
{
  GSList *p= NULL;

  LB::Event *myevent= new LB::Event();

  myevent->type= evt.type;
  myevent->source= evt.source->_duplicate(evt.source);
  myevent->value= evt.value;

  //printf ("-> addEvent\n");
  //printf ("add: lock\n");
  pthread_mutex_lock(&this->queue_lock);
  //printf ("add: locked\n");

  //print_queue();

  p= g_slist_append(this->event_queue_tail, myevent);

  if (this->event_queue_tail == NULL)
  {
    this->event_queue_head= p;
    this->event_queue_tail= p;
  }
  else
    this->event_queue_tail= p->next;

  //print_queue();

  //printf ("add: unlock\n");
  pthread_mutex_unlock(&this->queue_lock);
  //printf ("add: unlocked\n");
  //printf ("<- addEvent\n");
} // addEvent


void LB_Lightboard_i::do_run_events(void)
{
  GSList *p;

  while (1)
  {
    p= NULL;

    pthread_mutex_lock(&this->queue_lock);
    //      printf ("Mutex locked run\n");
    if (this->event_queue_head)
    {
      //printf ("there's a head\n");
      p= this->event_queue_head;
      //printf ("moving head\n");
      this->event_queue_head= p->next;
      //printf ("head moved\n");
      if (this->event_queue_head == NULL)
      {
        //printf ("no head anymore\n");
        this->event_queue_tail= NULL;
      }
    }
    pthread_mutex_unlock(&this->queue_lock);
    //printf ("Mutex unlocked run\n");

    if (p)
    {
      //printf ("there's an event\n");

      LB::Event *d= (LB::Event *)p->data;

      //printf ("got it's data\n");

      LB::EventSender_ptr src;
      src= LB::EventSender::_narrow(d->source);
      //printf ("narrowed\n");
      src->sendEvent(*d);
      //printf ("sent\n");
      delete d;
      //printf ("deleted\n");
      g_slist_free_1(p);
      //printf ("freed node\n");
    }
    else
    {
      usleep(10);
    }
  }
} // do_run_events
