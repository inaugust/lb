#ifndef _DIMMER_I_HH_
#define _DIMMER_I_HH_

#include "Dimmer.hh"
#include "Lightboard.hh"

int initialize_dimmers (LB::Lightboard_ptr lb);

class LB_Dimmer_i: public POA_LB::Dimmer,
                public PortableServer::RefCountServantBase {
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_Dimmer_i();

  char *my_name;
  char *my_device;
  int my_number;
  int my_handle;
  char *my_value;

public:
  // standard constructor
  LB_Dimmer_i(const char *name, const char *dev, int num);
  virtual ~LB_Dimmer_i();

  // methods corresponding to defined IDL attributes and operations
  char* name();
  char* device();
  CORBA::UShort number();
  void setValue(const char* value);
  char* getValue();
  
};

#endif _DIMMER_I_HH_
