#include "MovingInstrument_i.hh"
#include <math.h>

static void start(void *data, const char *el, const char **attr) 
{
  int i;
  const char *name, *dimmer, *xloc, *yloc, *zloc;

  if (strcmp(el, "moving_instrument")==0)
    {
      name=dimmer=xloc=yloc=zloc=NULL;
      for (i = 0; attr[i]; i += 2) 
        {
	  if (strcmp(attr[i],"name")==0)
            name=attr[i+1];
          if (strcmp(attr[i],"dimmer")==0)
            dimmer=attr[i+1];
          if (strcmp(attr[i],"xloc")==0)
            xloc=attr[i+1];
          if (strcmp(attr[i],"yloc")==0)
            yloc=attr[i+1];
          if (strcmp(attr[i],"zloc")==0)
            zloc=attr[i+1];
        }
      if (name && dimmer)
        {
	  int dnum = atoi(dimmer);
	  int xloc_m=10, yloc_m=10, zloc_m=10;
	  LB_MovingInstrument_i* i_i = new LB_MovingInstrument_i(name, dnum,
								 xloc_m,
								 yloc_m,
								 zloc_m);
	  /* This pointer won't ever be freed */
	  LB::MovingInstrument_ptr i_ref = i_i-> POA_LB::MovingInstrument::_this();
	  ((LB::Lightboard_ptr) data)->putInstrument(i_ref);
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
      perror("Moving Instruments");
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

int initialize_moving_instruments (LB::Lightboard_ptr lb)
{
  fprintf(stderr, "Initializing moving instruments\n");
  parse("instruments.xml", lb);
  fprintf(stderr, "Done initializing moving instruments\n");
}


LB_MovingInstrument_i::LB_MovingInstrument_i(const char *name, int dnum,
					     double xloc, double yloc,
					     double zloc): LB_Instrument_i (name, dnum)
{
  char dname[32];

  sprintf (dname, "%i", dimmer_start+1);
  this->x_dimmer=lb->getDimmer(dname);
  sprintf (dname, "%i", dimmer_start+2);
  this->y_dimmer=lb->getDimmer(dname);
 
  this->x_location=xloc;
  this->y_location=yloc;
  this->z_location=zloc;
  this->phi_correction=0.0;
  this->theta_correction=0.0;
  this->phi_delta=0.0;
  this->theta_delta=0.0;
}

LB_MovingInstrument_i::~LB_MovingInstrument_i()
{
}


void LB_MovingInstrument_i::xyz_to_xy(double tx, double ty, double tz,
	       long &outx, long &outy)
{
  // i is the instrument location
  double ix = this->x_location;
  double iy = this->y_location;
  double iz = this->z_location;
  // b is the instrument projected onto the xy plane
  double bx=this->x_location;
  double by=this->y_location;
  double bz=0.0;
  // p is target point projected onto the yz plane
  double px=0.0;
  double py=ty;
  double pz=tz;
  double sidea = sqrt( pow(ix-tx,2) + pow(iy-ty,2) + pow(iz-tz,2) );
  double sideb = sqrt( pow(ix-bx,2) + pow(iy-by,2) + pow(iz-bz,2) );
  double sidec = sqrt( pow(tx-bx,2) + pow(ty-by,2) + pow(tz-bz,2) );
  double phi=acos( (pow(sidea,2) + pow(sideb,2) - pow(sidec,2))/(2*sidea*sideb) );
  phi=phi + this->phi_correction;
        
  sideb = sqrt( pow(ix-px,2) + pow(iy-py,2) + pow(iz-pz,2) );
  sidec = sqrt( pow(tx-px,2) + pow(ty-py,2) + pow(tz-pz,2) );
  double theta=acos( (pow(sidea,2) + pow(sideb,2) - pow(sidec,2))/(2*sidea*sideb) );
  theta=theta+this->theta_correction;

  outy=long(phi/this->phi_delta);
  outx=long(theta/this->theta_delta);
}

void LB_MovingInstrument_i::setTarget(CORBA::Double x, CORBA::Double y, CORBA::Double z)
{
  long outx, outy;

  this->xyz_to_xy(x, y, z, outx, outy);
  this->x_dimmer->setValue(outx);
  this->x_dimmer->setValue(outy);
}

void LB_MovingInstrument_i::getTarget(CORBA::Double& x, CORBA::Double& y, CORBA::Double& z)
{
}
