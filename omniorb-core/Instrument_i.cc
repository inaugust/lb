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
  this->level_dimmer->setValue(level);

  /*
  LB::InstrumentUpdateEvent data;
  data.attr=LB::attr_level;
  data.value=level;

  CORBA::Any any;
  any <<= data;
  proxy_consumer->push(any);
  */
}

CORBA::Double LB_Instrument_i::getLevel()
{
  return this->my_level;
}

void LB_Instrument_i::setTarget(CORBA::Double x, CORBA::Double y, CORBA::Double z)
{
}

void LB_Instrument_i::getTarget(CORBA::Double& x, CORBA::Double& y, CORBA::Double& z)
{
}
