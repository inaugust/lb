#ifndef __GOBOROTATOR_HH__
#define __GOBOROTATOR_HH___

#include <Instrument.hh>
#include <Instrument_i.hh>
#include <Lightboard.hh>

#include <glib.h>

int initialize_gobo_rotators (LB::Lightboard_ptr lb);

class GoboRotator: //public POA_LB::Instrument,
		   //public PortableServer::RefCountServantBase
		   public LB_Instrument_i
{
protected:
  CORBA::Double my_gobo_rpm;

  //int dimmer_start;

  LB::Dimmer_ptr gobo_rpm_dimmer;
  
  /* null implementation */
  virtual void updateLevelFromSources();

public:

  // standard constructor
  GoboRotator(const char *name, int dimmer_start);
  virtual ~GoboRotator();

  // methods corresponding to defined IDL attributes and operations
  LB::AttrList* getAttributes();

  /* null implementation */
  virtual void setLevelFromSource(CORBA::Double level, const char* source);
  virtual void setLevel(CORBA::Double level);

  virtual void setGoboRPM(CORBA::Double rpm);
  virtual void getGoboRPM(CORBA::Double& rpm);

};


class GoboRotatorFactory: public POA_LB::InstrumentFactory,
			  public PortableServer::RefCountServantBase {
public:
  GoboRotatorFactory();
  virtual ~GoboRotatorFactory();

  LB::Instrument_ptr createInstrument(const char* name, 
				      const LB::ArgList& arguments);
};

#endif __GOBOROTATOR_HH__
