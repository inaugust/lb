#ifndef _DIMMER_I_HH_
#define _DIMMER_I_HH_

#include "lb.hh"

#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <errno.h>
#include <expat.h>
#include <glib.h>

int initialize_dimmers(CosNaming::NamingContext_ptr context);


class LB_Dimmer_i : public POA_LB::Dimmer,
                    public PortableServer::RefCountServantBase
{
private:
  // Make sure all instances are built on the heap by making the
  // destructor non-public
  //virtual ~LB_Dimmer_i();

  char *my_name;
  char *my_device;
  int  my_number;
  int  my_handle;
  double my_level;
  long my_value;

  int testfd;
public:
  // standard constructor
  LB_Dimmer_i(const char *name, const char *dev, int num);
  virtual ~LB_Dimmer_i();

  // methods corresponding to defined IDL attributes and operations
  char *name();
  char *device();
  CORBA::Long number();
  void setLevel(CORBA::Double level);
  CORBA::Double getLevel();
  void setValue(CORBA::Long value);
  CORBA::Long getValue();
};

#endif
