#include "CueFader_i.hh"
#include "lb.hh"

double interpolate_levels(double start, double end, double ratio)
{
  double r=start+((start-end)*ratio);
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
  this->start_cue=NULL;
  this->end_cue=NULL;
  this->instruments=NULL;
}

LB_CueFader_i::~LB_CueFader_i()
{
}


LB::Cue *duplicate_cue (const LB::Cue& incue)
{
  LB::Cue *cue = new LB::Cue;

  cue->name = incue.name;
  int numins=incue.ins.length();
  cue->ins.length(numins);
  for (int i=0; i<numins; i++)
    {
      cue->ins[i].name = incue.ins[i].name;
      int numattr=incue.ins[i].attrs.length();
      cue->ins[i].attrs.length(numattr);
      for (int a=0; a<numattr; a++)
	{
	  cue->ins[i].attrs[a].attr=incue.ins[i].attrs[a].attr;
	  int numval=incue.ins[i].attrs[a].value.length();
	  cue->ins[i].attrs[a].value.length(numval);
	  for (int v=0; v<numval; v++)
	    {
	      cue->ins[i].attrs[a].value[v]=incue.ins[i].attrs[a].value[v];
	    }
	}
    }
  
  return cue;
}

void LB_CueFader_i::setStartCue(const LB::Cue& incue)
{
  if (this->start_cue)
    delete this->start_cue;
  this->start_cue=duplicate_cue(incue);
}

void LB_CueFader_i::setEndCue(const LB::Cue& incue)
{
  if (this->end_cue)
    delete this->end_cue;
  this->end_cue=duplicate_cue(incue);

  if (this->instruments)
    free (this->instruments);
  this->instruments = (LB::Instrument_ptr *)malloc (sizeof (LB::Instrument_ptr) *
						incue.ins.length());
  for (int i=0; i<incue.ins.length(); i++)
    {
      this->instruments[i]=lb->getInstrument((char *)incue.ins[i].name);
    }
}

void LB_CueFader_i::setAttributes(const LB::AttrList& attr)
{
  int len=attr.length();
  this->attributes.length(len);
  for (int a=0; a<len; a++)
    {
      this->attributes[a]=attr[a];
    }
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

  LB::Cue *start=this->start_cue;
  LB::Cue *end=this->end_cue;

  double p1, p2, p3;
  int numins=end->ins.length();
  int i;
  int a;
  for (i=0; i<numins; i++)
    {
      int numattr=end_cue->ins[i].attrs.length();
      for (a=0; a<numattr; a++)
	{

	  if (!this->hasAttribute(end_cue->ins[i].attrs[a].attr))
	    continue;

	  if (end_cue->ins[i].attrs[a].attr==LB::attr_level)
	    {
	      p1=interpolate_levels(start_cue->ins[i].attrs[a].value[0],
				    end_cue->ins[i].attrs[a].value[0],
				    ratio);
	      
	      this->instruments[i]->setLevel(p1);
	    }

	  if (end_cue->ins[i].attrs[a].attr==LB::attr_target)
	    {
	      interpolate_targets(start_cue->ins[i].attrs[a].value[0],
				  start_cue->ins[i].attrs[a].value[1],
				  start_cue->ins[i].attrs[a].value[2],
				  end_cue->ins[i].attrs[a].value[0],
				  end_cue->ins[i].attrs[a].value[1],
				  end_cue->ins[i].attrs[a].value[2],
				  ratio,
				  p1, p2, p3);
	      
	      this->instruments[i]->setTarget(p1, p2, p3);
	    }
	}
    }
}


void LB_CueFader_i::clear()
{
}



/*
  printf ("cue %s %p\n",(char *)cue->name, &cue->name);

  int numins=cue->ins.length();
  printf ("instruments: %li\n", numins);
  for (int i=0; i<numins; i++)
    {
      printf ("  instrument: %s\n", (char *)cue->ins[i].name);
      int numattr=cue->ins[i].attrs.length();
      printf ("  attributes: %li\n", numattr);
      for (int a=0; a<numattr; a++)
	{
	  printf ("    %s=%s\n", (char *)cue->ins[i].attrs[a].attr,
		  (char *)cue->ins[i].attrs[a].value);
	}
    }

*/


/*

                  24.9
 without hasattr  23.7
 without strcmp   24.1
 without interpolate 11.75
 without setlevel  5
 */
