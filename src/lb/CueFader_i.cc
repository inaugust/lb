#include "CueFader_i.hh"
#include "lb.hh"

int initialize_cuefaders (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing cuefaders\n");

  LB_Fader_i* i_i = new LB_CueFader_i("C1");
  /* This pointer won't ever be freed */
  LB::Fader_ptr i_ref = i_i->_this();
  lb->putFader(i_ref);

  fprintf(stderr, "Done initializing cuefaders\n");

}


LB_CueFader_i::LB_CueFader_i(const char *name) : LB_Fader_i (name)
{
}

LB_CueFader_i::~LB_CueFader_i()
{
}

void LB_CueFader_i::setCues(const LB::Cue& startcue, const LB::Cue& endcue)
{
  normalize_cues (startcue, endcue, this->start_cue, this->end_cue);
  if (this->source_listeners)
    {
      LB::Event evt;
      evt.source=this->POA_LB::CueFader::_this();
      evt.value.length(0);
      evt.type=LB::event_fader_source;
      lb->addEvent(evt);
    }
}

void LB_CueFader_i::setAttributes(const LB::AttrList& attr)
{
  this->attributes=attr;
  /*
  int len=attr.length();
  this->attributes.length(len);
  for (int a=0; a<len; a++)
    {
      this->attributes[a]=attr[a];
    }
  */
}

int LB_CueFader_i::hasAttribute(LB::AttrType attr)
{
  int len=this->attributes.length();
  if (len==0)
    return 1;
  for (int a=0; a<len; a++)
    {
      if (this->attributes[a]==attr)
	return 1;
    }
  return 0;
}

void LB_CueFader_i::act_on_set_ratio (double ratio)
{
  //printf ("CueFader ratio %f\n", ratio);
  /* We assume the following:
     Each cue has the same of instruments, in the same order
     Each instrument has the same attributes, in the same order
  */

  LB::AttrValue data;
  int numins=end_cue.ins.length();
  int i;
  int a;
  for (i=0; i<numins; i++)
    {
      int numattr=end_cue.ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{

	  if (!this->hasAttribute(end_cue.ins[i].attrs[a].attr))
	    continue;

	  interpolate_attribute_values (start_cue.ins[i].attrs[a],
					end_cue.ins[i].attrs[a],
					ratio,
					data);
	  set_attribute_value (data, end_cue.ins[i].inst);
	}
    }
}


void LB_CueFader_i::clear()
{
  start_cue.ins.length(0);
  start_cue.name = CORBA::string_dup("");

  end_cue.ins.length(0);
  end_cue.name = CORBA::string_dup("");
}
