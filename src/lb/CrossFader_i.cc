#include "CrossFader_i.hh"

int initialize_crossfaders (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing crossfaders\n");

  LB_Fader_i* i_i = new LB_CrossFader_i("X1");
  /* This pointer won't ever be freed */
  LB::Fader_ptr i_ref = i_i->_this();
  lb->putFader(i_ref);

  fprintf(stderr, "Done initializing crossfaders\n");
}


LB_CrossFader_i::LB_CrossFader_i(const char * name) : LB_Fader_i (name)
{
}

LB_CrossFader_i::~LB_CrossFader_i()
{
}

static double my_time(void)
{
  struct timeval tv;
  gettimeofday(&tv, NULL);
  
  double r = tv.tv_sec + tv.tv_usec/1000000.0;
  return r;
}

static void print_cue(const LB::Cue& cue)
{
  printf ("  Name: %s\n", (char *)cue.name);
  for (int i=0; i<cue.ins.length(); i++)
    {
      printf ("  Instrument: %s\n", (char *)cue.ins[i].name);
      for (int a=0; a<cue.ins[i].attrs.length(); a++) 
	{
	  printf ("    Attribute: %d Value: %f\n", 
		  cue.ins[i].attrs[a].attr,
		  cue.ins[i].attrs[a].value[0]);
	}
    }
  printf ("  End\n");
}

void LB_CrossFader_i::setCues(const LB::Cue& downcue, const LB::Cue& upcue)
{
  double start, middle, end;

  printf ("Cue1\n");
  print_cue (downcue);
  printf ("Cue2\n");
  print_cue (upcue);

  start = my_time();
  if (this->instruments)
    {
      //release each of them;
      free (this->instruments);
    }

  normalize_cues (downcue, upcue, this->down_cue, this->up_cue);
  
  middle=my_time();

  this->instruments = (LB::Instrument_ptr *)malloc (sizeof (LB::Instrument_ptr) *
						    up_cue.ins.length());  
  
  for (int i=0; i<up_cue.ins.length(); i++)
    {
      this->instruments[i]=lb->getInstrument((char *)up_cue.ins[i].name);
    }
  end = my_time();


  printf ("%f %f %f\n", middle-start, end-middle, end-start);

  printf ("Cue1\n");
  print_cue (down_cue);
  printf ("Cue2\n");
  print_cue (up_cue);

}

void LB_CrossFader_i::setTimes(CORBA::Double downtime, CORBA::Double uptime)
{
  this->up_time=uptime;
  this->down_time=downtime;
}

char *LB_CrossFader_i::getUpCueName()
{
  CORBA::String_var ret;

  printf ("up:\n");
  if (strlen(this->up_cue.name))
    {
      printf ("up: %s\n", (char *)this->up_cue.name);
      ret=this->up_cue.name;   //also a String_, deep copy
    }
  else
    ret=CORBA::string_dup("");
  return ret._retn();
}

char *LB_CrossFader_i::getDownCueName()
{
  CORBA::String_var ret;

  printf ("down:\n");
  if (strlen(this->down_cue.name))
    {
      printf ("down: %s\n", (char *)this->down_cue.name);
      ret=this->down_cue.name;
    }
  else
    ret=CORBA::string_dup("");
  return ret._retn();
}

void LB_CrossFader_i::act_on_set_ratio (double ratio)
{
  double utr, dtr, r;

  utr = this->intime / this->up_time;
  dtr = this->intime / this->down_time;

  if (utr<1.0 || dtr<1.0)
    {
      if(utr<dtr)
	{
	  r=1.0/utr;
	  dtr=r*dtr;
	}
      else
	{
	  r=1.0/dtr;
	  utr=r*utr;
	}
    }

  utr=utr*ratio;
  dtr=dtr*ratio;

  if (utr>1.0) utr=1.0;
  if (utr<0.0) utr=0.0;
  if (dtr>1.0) dtr=1.0;
  if (dtr<0.0) dtr=0.0;

  dtr=1.0-dtr;

  double p1, p2;
  int i;
  int a;
  int numins;

  CORBA::String_var name=this->name();

  numins = up_cue.ins.length();
  for (i=0; i<numins; i++)
    {
      int numattr=up_cue.ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{
	  if (up_cue.ins[i].attrs[a].attr==LB::attr_level)
	    {
	      p1 = down_cue.ins[i].attrs[a].value[0] * dtr;
	      p2 = up_cue.ins[i].attrs[a].value[0] * utr;
	      this->instruments[i]->setLevelFromSource(p1+p2, name);
	    }
	}
    }
}


void LB_CrossFader_i::clear()
{
}
