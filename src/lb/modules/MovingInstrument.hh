#include <iostream.h>
#include "MovingInstrument.hh"
#include "Instrument_i.hh"
#include "lb.hh"

int initialize_moving_instruments(LB::Lightboard_ptr lb);


class LB_MovingInstrument_i : public POA_LB::MovingInstrument,
//                public PortableServer::RefCountServantBase
                              public LB_Instrument_i
{
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_MovingInstrument_i();

  double x_location;
  double y_location;
  double z_location;
  double phi_correction;
  double theta_correction;

  double phi_delta;
  double theta_delta;

  LB::Dimmer_ptr x_dimmer;
  LB::Dimmer_ptr y_dimmer;

  void xyz_to_xy(double inx, double iny, double inz, long& outx, long& outy);


public:
  // standard constructor
  LB_MovingInstrument_i(const char *name, int dnum,
                        double xloc, double yloc,
                        double zloc);
  virtual ~LB_MovingInstrument_i();

  // methods corresponding to defined IDL attributes and operations

  void setTarget(CORBA::Double x, CORBA::Double y, CORBA::Double z);
  void getTarget(CORBA::Double& x, CORBA::Double& y, CORBA::Double& z);


  /*
   *  char* name();
   *  LB::AttrList* getAttributes();
   *  void setLevel(const char* level);
   *  char* getLevel();
   */
};
