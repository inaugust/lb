#include "LevelFader_i.hh"

int initialize_levelfaders (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing levelfaders\n");

  LB_Fader_i* i_i = new LB_LevelFader_i("L1");
  /* This pointer won't ever be freed */
  LB::Fader_ptr i_ref = i_i->_this();
  lb->putFader(i_ref);

  fprintf(stderr, "Done initializing levelfaders\n");
}

LB_LevelFader_i::LB_LevelFader_i(const char * name) : LB_Fader_i (name)
{
  this->instruments=NULL;
}

LB_LevelFader_i::~LB_LevelFader_i()
{
}

void LB_LevelFader_i::setCue(const LB::Cue& incue)
{
  this->cue=incue;  // Deep copy, I suspect.

  if (this->instruments)
    free (this->instruments);
  this->instruments = (LB::Instrument_ptr *)malloc (sizeof (LB::Instrument_ptr) *
						    incue.ins.length());
  for (int i=0; i<incue.ins.length(); i++)
    this->instruments[i]=lb->getInstrument((char *)incue.ins[i].name);
}


void LB_LevelFader_i::act_on_set_ratio (double ratio)
{
  double p1;
  int i;
  int a;
  int numins;

  numins = cue.ins.length();
  for (i=0; i<numins; i++)
    {
      int numattr=cue.ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{
	  if (cue.ins[i].attrs[a].attr==LB::attr_level)
	    {
	      p1 = cue.ins[i].attrs[a].value[0] * ratio;
	      
	      this->instruments[i]->setLevelFromSource(p1, this->name());
	    }
	}
    }
}


void LB_LevelFader_i::clear()
{
}

