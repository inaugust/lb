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

LB_Lightboard_i::LB_Lightboard_i()
{
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

void LB_Lightboard_i::addEvent(LB::Event& evt)
  /* 
     Queues up an event.  We take ownership of the event structure.
     Allocate it with new, and don't use it after you pass it in. 
  */
{
  GSList *p=NULL;

  //  printf ("-> addEvent\n");
  //  printf ("add: lock\n");
  pthread_mutex_lock(&this->queue_lock);
  //  printf ("add: locked\n");

  //  print_queue();

  p = g_slist_append(this->event_queue_tail, &evt);

  if (this->event_queue_tail == NULL)
    {
      this->event_queue_head = p;
      this->event_queue_tail = p;
    }
  else
    this->event_queue_tail = p->next;

  //  print_queue();

  //  printf ("add: unlock\n");
  pthread_mutex_unlock(&this->queue_lock);
  //  printf ("add: unlocked\n");
  //  printf ("<- addEvent\n");
}


void LB_Lightboard_i::do_run_events(void)
{
  GSList *p;

  while (1)
    {
      p = NULL;

      //      printf ("do run: lock\n");
      pthread_mutex_lock(&this->queue_lock);
      //      printf ("do run: locked\n");

      //      print_queue();

      if (this->event_queue_head)
	{
	  //  printf ("do run: event!\n");
	  p=this->event_queue_head;
	  this->event_queue_head=p->next;
	  if (this->event_queue_head==NULL)
	    this->event_queue_tail=NULL;
	}
      
      //      print_queue();
      //      printf ("do run: unlock\n");
      pthread_mutex_unlock(&this->queue_lock);
      //      printf ("do run: unlocked\n");
      if (p)
	{
	  LB::Event *d = (LB::Event *)p->data;

	  switch (d->type)
	    {
	    case LB::event_instrument_level:
	      //	      printf ("do run: level event!\n");
	      LB::Instrument_ptr src;
	      src = LB::Instrument::_narrow(d->source);
	      src->doFireLevelEvent(*d);
	      break;
	    }
	  //	  printf ("do run: free\n");
	  delete d;
	  g_slist_free_1(p);
	}
      else
	{
	  //	  printf ("do run: sleep\n");
	  usleep(10);
	  //	  printf ("do run: wake\n");
	}
    }
}
