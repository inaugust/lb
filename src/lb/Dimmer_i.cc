#include "Dimmer_i.hh"

static GHashTable *dimmer_devices;

static pthread_mutex_t write_lock;

static void start(void *data, const char *el, const char **attr) 
{
  int i;
  const char *dev, *dimmers, *start;
  CosNaming::NamingContext_ptr context=(CosNaming::NamingContext_ptr) data;
  CosNaming::Name cname;
  cname.length(1);

  if (strcmp(el, "dimmerbank")==0)
    {
      dev=dimmers=start=NULL;
      for (i = 0; attr[i]; i += 2) 
        {
	  if (strcmp(attr[i],"dev")==0)
            dev=attr[i+1];
          if (strcmp(attr[i],"dimmers")==0)
            dimmers=attr[i+1];
          if (strcmp(attr[i],"start")==0)
            start=attr[i+1];
        }
      if (dev && dimmers)
        {
          int num = atoi(dimmers);
          int startnum;
          if (start)
            int startnum = atoi(start);
          else
            startnum=1;
          char name[32];

          printf ("Dimmers range from %i to %i\n", startnum, startnum+num-1);
          for (int i=startnum; i<startnum+num; i++)
            {
              sprintf(name, "%i", i);

              LB_Dimmer_i* d_i = new LB_Dimmer_i(name, dev, i-startnum);
              /* This pointer won't ever be freed */
              LB::Dimmer_ptr d_ref = d_i->_this();

	      cname[0].id   = (const char *)name;
	      cname[0].kind   = (const char *)"Dimmer";
	      context->rebind(cname, d_ref);
            }
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
      perror("Dimmers");
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

int initialize_dimmers (CosNaming::NamingContext_ptr context)
{
  fprintf(stderr, "Initializing dimmers\n");
  dimmer_devices=g_hash_table_new (g_str_hash, g_str_equal);
  pthread_mutex_init (&write_lock, NULL);
  parse("/etc/lb/config.xml", context);
  fprintf(stderr, "Done initializing dimmers\n");
}


LB_Dimmer_i::LB_Dimmer_i(const char *name, const char *device, int number)
{
  this->my_name=strdup(name);
  this->my_device=strdup(device);
  this->my_number=number;
  this->my_value=0;
  this->my_level=0.0;

  int dev=(int)g_hash_table_lookup(dimmer_devices, device);

  if (dev==0)
    {
      dev=open(device, O_RDWR | O_SYNC);
      if (dev==-1)
        {
          perror ("Dimmer");
        }
      g_hash_table_insert (dimmer_devices, strdup(device), (gpointer)dev);
    }
  this->my_handle=dev;
  this->testfd=0;
}

LB_Dimmer_i::~LB_Dimmer_i()
{
  if (this->testfd)
    close(this->testfd);
}


char* LB_Dimmer_i::name()
{
  CORBA::String_var ret;

  ret=CORBA::string_dup(this->my_name);
  return ret._retn();
}

char* LB_Dimmer_i::device()
{
  CORBA::String_var ret;

  ret=CORBA::string_dup(this->my_device);
  return ret._retn();
}

CORBA::Long LB_Dimmer_i::number()
{
  return this->my_number;
}

void LB_Dimmer_i::setLevel(CORBA::Double level)
{
  this->my_level=level;
  this->my_value=long((level/100.0)*255);
}

CORBA::Double LB_Dimmer_i::getLevel()
{
  return my_level;
}


double my_time2(void)
{
  struct timeval tv;
  gettimeofday(&tv, NULL);
  
  double r = tv.tv_sec + tv.tv_usec/1000000.0;
  return r;
}


void LB_Dimmer_i::setValue(CORBA::Long value)
{
  this->my_value=value;
  char buf[256];
  unsigned char val = (unsigned char)value;

  pthread_mutex_lock(&write_lock);
  lseek(this->my_handle, this->my_number, SEEK_SET);
  write(this->my_handle, &val, 1);
  pthread_mutex_unlock(&write_lock);
}

CORBA::Long LB_Dimmer_i::getValue()
{
  return my_value;
}

// End of example implementational code
