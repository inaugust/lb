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
}

LB_LevelFader_i::~LB_LevelFader_i()
{
}

void LB_LevelFader_i::setCue(const LB::Cue& incue)
{
  this->cue=incue;  // Deep copy, I suspect.
}


void LB_LevelFader_i::act_on_set_ratio (double ratio)
{
  double p1;
  int i;
  int a;
  int numins;

  CORBA::String_var name=this->name();

  numins = cue.ins.length();
  for (i=0; i<numins; i++)
    {
      int numattr=cue.ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{
	  if (cue.ins[i].attrs[a].attr==LB::attr_level)
	    {
	      p1 = cue.ins[i].attrs[a].value[0] * ratio;
	      
	      cue.ins[i].inst->setLevelFromSource(p1, name);
	    }
	}
    }
}


void LB_LevelFader_i::clear()
{
  cue.ins.length(0);
  cue.name = CORBA::string_dup("");
}

