#include "CrossFader_i.hh"

int initialize_crossfaders (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing crossfaders\n");
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
      printf ("  Instrument: %s %s\n", (char *)cue.ins[i].name,
	      (char *)cue.ins[i].inst->name());
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
  printf ("Cue1\n");
  print_cue (downcue);
  printf ("Cue2\n");
  print_cue (upcue);

  normalize_cues (downcue, upcue, this->down_cue, this->up_cue);

  printf ("Cue1\n");
  print_cue (down_cue);
  printf ("Cue2\n");
  print_cue (up_cue);

  if (this->source_listeners)
    {
      printf ("hi\n");
      LB::Event evt;
      evt.source=this->POA_LB::CrossFader::_this();
      evt.value.length(0);
      evt.type=LB::event_fader_source;
      lb->addEvent(evt);
    }
}

void LB_CrossFader_i::setTimes(CORBA::Double downtime, CORBA::Double uptime)
{
  this->up_time=uptime;
  this->down_time=downtime;
}

char *LB_CrossFader_i::getUpCueName()
{
  CORBA::String_var ret;

  if (strlen(this->up_cue.name))
    {
      ret=this->up_cue.name;   //also a String_, deep copy
    }
  else
    ret=CORBA::string_dup("");
  return ret._retn();
}

char *LB_CrossFader_i::getDownCueName()
{
  CORBA::String_var ret;

  if (strlen(this->down_cue.name))
    {
      ret=this->down_cue.name;
    }
  else
    ret=CORBA::string_dup("");
  return ret._retn();
}

CORBA::Double LB_CrossFader_i::getUpCueTime()
{
  return up_time;
}

CORBA::Double LB_CrossFader_i::getDownCueTime()
{
  return down_time;
}

void LB_CrossFader_i::act_on_set_ratio (double ratio)
{
  double utr, dtr, r;
  double myintime = intime;

  //  printf ("CrossFader ratio %f\n", ratio);

  if (myintime == 0.0)
    myintime = 1;

  utr = myintime / this->up_time;
  dtr = myintime / this->down_time;

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
	      /*
	      printf ("CF: (%f*%f)=%f + (%f*%f)=%f  == %f\n",   
		      down_cue.ins[i].attrs[a].value[0], dtr, p1,
		      up_cue.ins[i].attrs[a].value[0], utr,p2,
		      p1+p2);
	      */
	      up_cue.ins[i].inst->setLevelFromSource(p1+p2, name);
	    }
	}
    }
}


void LB_CrossFader_i::clear()
{
  int i, a, numins;
  numins = up_cue.ins.length();

  CORBA::String_var name=this->name();

  for (i=0; i<numins; i++)
    {
      int numattr=up_cue.ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{
	  if (up_cue.ins[i].attrs[a].attr==LB::attr_level)
	    {
	      up_cue.ins[i].inst->setLevelFromSource(0.0, name);
	    }
	}
    }

  down_cue.ins.length(0);
  down_cue.name = CORBA::string_dup("");

  up_cue.ins.length(0);
  up_cue.name = CORBA::string_dup("");
  this->setLevel(0.0);
}
