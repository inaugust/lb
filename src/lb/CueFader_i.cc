#include "CueFader_i.hh"
#include "lb.hh"

double interpolate_levels(double start, double end, double ratio)
{
  double r=start+((end-start)*ratio);
  //  printf ("%f, %f: %f+%f=%f\n", end, ratio, start, (end-start)*ratio, r);
  return r;
}

void interpolate_targets(double sx, double sy, double sz,
			 double ex, double ey, double ez,
			 double ratio,
			 double &ox, double &oy, double &oz)
{
  ox=(ex-sx)*ratio;
  oy=(ey-sy)*ratio;
  oz=(ez-sz)*ratio;
}

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

  double p1, p2, p3;
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

	  if (end_cue.ins[i].attrs[a].attr==LB::attr_level)
	    {
	      p1=interpolate_levels(start_cue.ins[i].attrs[a].value[0],
				    end_cue.ins[i].attrs[a].value[0],
				    ratio);
	      
	      end_cue.ins[i].inst->setLevel(p1);
	    }

	  if (end_cue.ins[i].attrs[a].attr==LB::attr_target)
	    {
	      interpolate_targets(start_cue.ins[i].attrs[a].value[0],
				  start_cue.ins[i].attrs[a].value[1],
				  start_cue.ins[i].attrs[a].value[2],
				  end_cue.ins[i].attrs[a].value[0],
				  end_cue.ins[i].attrs[a].value[1],
				  end_cue.ins[i].attrs[a].value[2],
				  ratio,
				  p1, p2, p3);
	      
	      end_cue.ins[i].inst->setTarget(p1, p2, p3);
	    }
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
