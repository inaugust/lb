#include "LevelFader_i.hh"

int initialize_levelfaders (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing levelfaders\n");
  fprintf(stderr, "Done initializing levelfaders\n");
}

LB_LevelFader_i::LB_LevelFader_i(const char * name) : LB_Fader_i (name)
{
}

LB_LevelFader_i::~LB_LevelFader_i()
{
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


void LB_LevelFader_i::setCue(const LB::Cue& incue)
{
  this->cue=incue;  // Deep copy, I suspect.
  printf ("set\n");
  if (this->source_listeners)
    {
      printf ("source evt\n");
      LB::Event evt;
      evt.source=this->POA_LB::LevelFader::_this();
      evt.value.length(0);
      evt.type=LB::event_fader_source;
      lb->addEvent(evt);
    }
}

char *LB_LevelFader_i::getCueName()
{
  CORBA::String_var ret;

  if (strlen(this->cue.name))
    {
      ret=this->cue.name;   //also a String_, deep copy
    }
  else
    ret=CORBA::string_dup("");
  return ret._retn();
}

void LB_LevelFader_i::act_on_set_ratio (double ratio)
{
  double p1;
  int i;
  int a;
  int numins;

  CORBA::String_var myname=this->name();

  //printf ("Levelfader %s myname @ %f\n", (const char *)myname, ratio);

  numins = cue.ins.length();
  for (i=0; i<numins; i++)
    {
      //printf ("Levelfader ins %i\n", i);
      int numattr=cue.ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{
	  if (cue.ins[i].attrs[a].attr==LB::attr_level)
	    {
	      p1 = cue.ins[i].attrs[a].value[0] * ratio;
	      //printf ("Levelfader ins @ %f\n", p1);

	      cue.ins[i].inst->setLevelFromSource(p1, myname);
	      //printf ("Done Levelfader ins @ %f\n", p1);	      
	    }
	}
    }
}


void LB_LevelFader_i::clear()
{
  this->setLevel(0.0);
  cue.ins.length(0);
  cue.name = CORBA::string_dup("");
}

