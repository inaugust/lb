//
// Example code for implementing IDL interfaces in file Dimmer.idl
//

#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <errno.h>
#include <expat.h>
#include <sys/time.h>

#include <string>

#include "Dimmer_i.hh"
#include "lb.hh"

static map<const char *, int, ltstr> dimmer_devices;

static void start(void *data, const char *el, const char **attr) 
{
  int i;
  const char *dev, *dimmers, *start;

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
              ((LB::Lightboard_ptr) data)->putDimmer(d_ref);
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

int initialize_dimmers (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing dimmers\n");
  parse("dimmers.xml", lb);
  fprintf(stderr, "Done initializing dimmers\n");
}

//
// Example implementational code for IDL interface LB::Dimmer
//
LB_Dimmer_i::LB_Dimmer_i(const char *name, const char *device, int number)
{
  this->my_name=strdup(name);
  this->my_device=strdup(device);
  this->my_number=number;
  this->my_value=0;
  this->my_level=0.0;
  int dev=dimmer_devices[device];
  if (dev==0)
    {
      dev=open(device, O_RDWR | O_SYNC);
      if (dev==-1)
        {
          perror ("Dimmer");
        }
      dimmer_devices[device]=dev;
      // we need a mutex here
    }
  this->my_handle=dev;
  this->testfd=0;
  if (!strcmp(name, "1"))
    this->testfd=open("/tmp/dimmer1", O_RDWR | O_TRUNC |O_CREAT, 
		      S_IREAD | S_IWRITE);
  if (!strcmp(name, "2"))
    this->testfd=open("/tmp/dimmer2", O_RDWR | O_TRUNC |O_CREAT,
		      S_IREAD | S_IWRITE);
}

LB_Dimmer_i::~LB_Dimmer_i(){
  // add extra destructor code here
  if (this->testfd)
    close(this->testfd);
}
//   Methods corresponding to IDL attributes and operations
char* LB_Dimmer_i::name()
{
  return this->my_name;
}

char* LB_Dimmer_i::device()
{
  return this->my_device;
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

  if (this->testfd)
    {
      double t = my_time2();
      sprintf (buf, "%f %li\n", t, value);
      write (this->testfd, buf, strlen(buf));
    }

  // lock
  // lseek(this->my_handle, this->my_number, SEEK_SET);
  // write(this->my_handle, &level, 1);
  // flush?
  // unlock
}

CORBA::Long LB_Dimmer_i::getValue()
{
}

// End of example implementational code
