//
// Example code for implementing IDL interfaces in file Instrument.idl
//

#include <string>

#include "lb.hh"
#include "Instrument_i.hh"

static void start(void *data, const char *el, const char **attr) 
{
  int i;
  const char *name, *dimmer;

  if (strcmp(el, "instrument")==0)
    {
      name=dimmer=NULL;
      for (i = 0; attr[i]; i += 2) 
        {
	  if (strcmp(attr[i],"name")==0)
            name=attr[i+1];
          if (strcmp(attr[i],"dimmer")==0)
            dimmer=attr[i+1];
        }
      if (name && dimmer)
        {
	  int dnum = atoi(dimmer);
	  LB_Instrument_i* i_i = new LB_Instrument_i(name, dnum);
	  /* This pointer won't ever be freed */
	  LB::Instrument_ptr i_ref = i_i->_this();
	  ((LB::Lightboard_ptr) data)->putInstrument(i_ref);
        }
    }
}

static void end(void *data, const char *el) 
{
}

static void parse (const char *fn, void *userdata)
{
  char buf[8096];

  XML_Parser p = XML_ParserCreate(NULL);
  if (!p) 
    {
      fprintf(stderr, "Couldn't allocate memory for parser\n");
      exit(-1);
    }

  XML_SetUserData(p, userdata);

  XML_SetElementHandler(p, start, end);
  FILE *f = fopen(fn, "r");
  if (!f)
    {
      perror("Instruments");
      exit(-1);
    }

  for (;;) {
    int done;
    int len;

    len = fread(buf, 1, 8096, f);
    if (ferror(f)) {
      fprintf(stderr, "Read error\n");
      exit(-1);
    }
    done = feof(f);

    if (! XML_Parse(p, buf, len, done)) {
      fprintf(stderr, "Parse error at line %d:\n%s\n",
              XML_GetCurrentLineNumber(p),
              XML_ErrorString(XML_GetErrorCode(p)));
      exit(-1);
    }

    if (done)
      break;
  }
  fclose(f);
}

int initialize_instruments (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing instruments\n");
  parse("instruments.xml", lb);
  fprintf(stderr, "Done initializing instruments\n");
}

LB_Instrument_i::LB_Instrument_i(const char *name, int dimmer_start)
{
  char dname[32];
  this->my_name=strdup(name);
  this->my_level=0L;
 
  this->dimmer_start=dimmer_start;
  sprintf (dname, "%i", dimmer_start);
  this->level_dimmer=lb->getDimmer(dname);

  pthread_mutex_init (&this->listener_lock, NULL);

  this->level_listeners=NULL;
  this->target_listeners=NULL;

  /*
  printf ("Instrument %s, at %i, dimmer %p\n", this->my_name, 
	  this->dimmer_start,
	  this->level_dimmer);
  */
}

LB_Instrument_i::~LB_Instrument_i()
{
  // add extra destructor code here
}

char* LB_Instrument_i::name()
{
  return this->my_name;
}

LB::AttrList* LB_Instrument_i::getAttributes()
{

}

void LB_Instrument_i::setLevel(CORBA::Double level)
{
  this->my_level=level;
  this->level_dimmer->setValue((long)((level/100.0)*255.0));
  if (this->level_listeners)
    {
      LB::Event *evt = new LB::Event();

      evt->source=this->_this();
      evt->value.length(1);
      evt->value[0]=level;
      evt->type=LB::event_instrument_level;

      lb->addEvent(*evt);
    }
}

CORBA::Double LB_Instrument_i::getLevel()
{
  return this->my_level;
}

void LB_Instrument_i::doFireLevelEvent(const LB::Event &evt)
{
  pthread_mutex_lock(&this->listener_lock);
  GSList *list = this->level_listeners;
  while (list)
    {
      ((LB::InstrumentLevelListener_ptr) list->data)->levelChanged(evt);
      list=list->next;
    }
  pthread_mutex_unlock(&this->listener_lock);
}

void LB_Instrument_i::addLevelListener(const char *l)
{
  pthread_mutex_lock(&this->listener_lock);

  printf ("l = %s\n", l);
  CORBA::Object_var obj = orb->string_to_object(l);
  //  printf ("obj = %p\n", obj);
  LB::InstrumentLevelListener_ptr p = LB::InstrumentLevelListener::_narrow(obj);
  printf ("p = %p\n", p);

  this->level_listeners=g_slist_append(this->level_listeners, p);
  pthread_mutex_unlock(&this->listener_lock);
}

void LB_Instrument_i::removeLevelListener(const char *l)
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

void LB_Instrument_i::doFireTargetEvent(const LB::Event &evt)
{
}

void LB_Instrument_i::addTargetListener(const char *l)
{
  pthread_mutex_lock(&this->listener_lock);
  //  this->target_listeners=g_slist_append(this->target_listeners, l);
  pthread_mutex_unlock(&this->listener_lock);
}

void LB_Instrument_i::removeTargetListener(const char *l)
{
  pthread_mutex_lock(&this->listener_lock);
  pthread_mutex_unlock(&this->listener_lock);
}
