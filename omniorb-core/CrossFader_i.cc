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
  this->up_cue=NULL;
  this->down_cue=NULL;
}

LB_CrossFader_i::~LB_CrossFader_i()
{
}

void LB_CrossFader_i::setUpCue(const LB::Cue& incue, CORBA::Double time)
{
  if (this->up_cue)
    delete this->up_cue;
  this->up_cue=duplicate_cue(incue, 0);
  this->up_time=time;
}

void LB_CrossFader_i::setDownCue(const LB::Cue& incue, CORBA::Double time)
{
  if (this->down_cue)
    delete this->down_cue;
  this->down_cue=duplicate_cue(incue, 0);
  this->down_time=time;

  if (this->instruments)
    free (this->instruments);
  
  this->instruments = (LB::Instrument_ptr *)malloc (sizeof (LB::Instrument_ptr) *
						    incue.ins.length());
  
  for (int i=0; i<incue.ins.length(); i++)
    this->instruments[i]=lb->getInstrument((char *)incue.ins[i].name);
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

  numins = down_cue->ins.length();
  for (i=0; i<numins; i++)
    {
      int numattr=down_cue->ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{
	  if (down_cue->ins[i].attrs[a].attr==LB::attr_level)
	    {
	      p1 = down_cue->ins[i].attrs[a].value[0] * dtr;
	      p2 = up_cue->ins[i].attrs[a].value[0] * utr;
	      
	      this->instruments[i]->setLevelFromSource(p1+p2, this->name());
	    }
	}
    }
}


void LB_CrossFader_i::clear()
{
}
