//
// Example code for implementing IDL interfaces in file Lightboard.idl
//

#include "Lightboard_i.hh"
#include <unistd.h>
#include <stdio.h>

extern "C"
{
  static void *bootstrap(void *object)
  {
    ((LB_Lightboard_i *)object)->do_run_events();
  }
}

LB_Lightboard_i::LB_Lightboard_i(const char *name)
{
  this->my_name=strdup(name);

  pthread_mutex_init (&this->queue_lock, NULL);

  pthread_create(&this->event_thread, (pthread_attr_t *)NULL,
		 bootstrap,
		 this);
}

LB_Lightboard_i::~LB_Lightboard_i()
{
}

//   Methods corresponding to IDL attributes and operations
CORBA::ULong LB_Lightboard_i::dimmerRange()
{
  return 255;
}

char* LB_Lightboard_i::name()
{
  CORBA::String_var ret;

  ret=CORBA::string_dup(this->my_name);
  return ret._retn();
}

LB::Instrument_ptr LB_Lightboard_i::getInstrument(const char* name)
{
  return LB::Instrument::_duplicate (this->instruments[name]);
}

void LB_Lightboard_i::putInstrument(LB::Instrument_ptr ins)
{
  this->instruments[ins->name()] = ins;
}

LB::Fader_ptr LB_Lightboard_i::getFader(const char* name)
{
  return LB::Fader::_duplicate (this->faders[name]);
}

void LB_Lightboard_i::putFader(LB::Fader_ptr fadr)
{
  this->faders[fadr->name()] = fadr;
}

LB::Dimmer_ptr LB_Lightboard_i::getDimmer(const char* name)
{
  return LB::Dimmer::_duplicate (this->dimmers[name]);
}

void LB_Lightboard_i::putDimmer(LB::Dimmer_ptr dimr)
{
  this->dimmers[dimr->name()] = dimr;
}

CORBA::Long LB_Lightboard_i::createInstrument(const char* show, 
					      const char* name, 
					      CORBA::Long dimmer_start)
{
  CosNaming::Name cname;
  cname.length(1);
  
  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  //  printf ("Creating instrument for show: %s named: %s dimmer %li\n",
  //	  show, name, dimmer_start);

  LB_Instrument_i* i_i = new LB_Instrument_i(name, dimmer_start);
  LB::Instrument_var i_ref = i_i->_this();


  try
    {
      cname[0].id   = (const char *)"shows";
      obj=rootNaming->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)show;
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)"instruments";
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

    }
  catch (...)
    {
      printf ("Can't get instrument context\n");
      return 1;
    }

  cname[0].id   = (const char *)name;
  cname[0].kind   = (const char *)"Instrument";

  try 
    {
      context->bind(cname, i_ref);
    }
  catch(CosNaming::NamingContext::AlreadyBound& ex) 
    {
      context->rebind(cname, i_ref);
    }
  return 0;
}

CORBA::Long LB_Lightboard_i::createLevelFader(const char* show, 
					      const char* name)
{
  CosNaming::Name cname;
  cname.length(1);
  
  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  printf ("Creating levelfader for show: %s named: %s\n",
  	  show, name);

  LB_Fader_i* i_i = new LB_LevelFader_i(name);
  LB::Fader_var i_ref = i_i->_this();

  try
    {
      cname[0].id   = (const char *)"shows";
      obj=rootNaming->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)show;
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)"faders";
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

    }
  catch (...)
    {
      printf ("Can't get fader context\n");
      return 1;
    }

  cname[0].id   = (const char *)name;
  cname[0].kind   = (const char *)"Fader";

  try 
    {
      context->bind(cname, i_ref);
    }
  catch(CosNaming::NamingContext::AlreadyBound& ex) 
    {
      context->rebind(cname, i_ref);
    }
  printf ("done\n");
  return 0;
}

CORBA::Long LB_Lightboard_i::createCueFader(const char* show, 
					    const char* name)
{
  CosNaming::Name cname;
  cname.length(1);
  
  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  printf ("Creating cuefader for show: %s named: %s\n",
  	  show, name);

  LB_Fader_i* i_i = new LB_CueFader_i(name);
  LB::Fader_var i_ref = i_i->_this();

  try
    {
      cname[0].id   = (const char *)"shows";
      obj=rootNaming->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)show;
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)"faders";
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

    }
  catch (...)
    {
      printf ("Can't get fader context\n");
      return 1;
    }

  cname[0].id   = (const char *)name;
  cname[0].kind   = (const char *)"Fader";

  try 
    {
      context->bind(cname, i_ref);
    }
  catch(CosNaming::NamingContext::AlreadyBound& ex) 
    {
      context->rebind(cname, i_ref);
    }
  printf ("done\n");
  return 0;
}

CORBA::Long LB_Lightboard_i::createCrossFader(const char* show, 
					      const char* name)
{
  CosNaming::Name cname;
  cname.length(1);
  
  CosNaming::NamingContext_var context;
  CORBA::Object_var obj;

  printf ("Creating crossfader for show: %s named: %s\n",
  	  show, name);

  LB_Fader_i* i_i = new LB_CrossFader_i(name);
  LB::Fader_var i_ref = i_i->_this();

  try
    {
      cname[0].id   = (const char *)"shows";
      obj=rootNaming->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)show;
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

      cname[0].id   = (const char *)"faders";
      obj=context->resolve(cname);
      context = CosNaming::NamingContext::_narrow(obj);

    }
  catch (...)
    {
      printf ("Can't get fader context\n");
      return 1;
    }

  cname[0].id   = (const char *)name;
  cname[0].kind   = (const char *)"Fader";

  try 
    {
      context->bind(cname, i_ref);
    }
  catch(CosNaming::NamingContext::AlreadyBound& ex) 
    {
      context->rebind(cname, i_ref);
    }
  printf ("done\n");
  return 0;
}




void LB_Lightboard_i::print_queue(void)
{
  printf ("head: %p tail: %p\n", event_queue_head, event_queue_tail);
  int i=0;
  GSList *l = event_queue_head;
  while (l)
    {
      printf ("%i %p\n", i, l);
      l=l->next;
      i++;
    }
  printf ("end of queue\n");
}

void LB_Lightboard_i::addEvent(const LB::Event& evt)
{
  GSList *p=NULL;

  LB::Event *myevent = new LB::Event();
  myevent->type=evt.type;
  myevent->source=evt.source->_duplicate(evt.source);
  myevent->value=evt.value;

  //printf ("-> addEvent\n");
  //printf ("add: lock\n");
  pthread_mutex_lock(&this->queue_lock);
  //printf ("add: locked\n");

  //print_queue();

  p = g_slist_append(this->event_queue_tail, myevent);

  if (this->event_queue_tail == NULL)
    {
      this->event_queue_head = p;
      this->event_queue_tail = p;
    }
  else
    this->event_queue_tail = p->next;

  //print_queue();

  //printf ("add: unlock\n");
  pthread_mutex_unlock(&this->queue_lock);
  //printf ("add: unlocked\n");
  //printf ("<- addEvent\n");
}


void LB_Lightboard_i::do_run_events(void)
{
  GSList *p;

  while (1)
    {
      p = NULL;

      pthread_mutex_lock(&this->queue_lock);
      //      printf ("Mutex locked run\n");
      if (this->event_queue_head)
	{
	  //printf ("there's a head\n");
	  p=this->event_queue_head;
	  //printf ("moving head\n");
	  this->event_queue_head=p->next;
	  //printf ("head moved\n");
	  if (this->event_queue_head==NULL)
	    {
	      //printf ("no head anymore\n");
	      this->event_queue_tail=NULL;
	    }
	}
      pthread_mutex_unlock(&this->queue_lock);
      //printf ("Mutex unlocked run\n");      

      if (p)
	{
	  //printf ("there's an event\n");      
		
	  LB::Event *d = (LB::Event *)p->data;

	  //printf ("got it's data\n");

	  LB::EventSender_ptr src;
	  src = LB::EventSender::_narrow(d->source);
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
}




