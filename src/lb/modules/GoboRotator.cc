#include <string>

#include <lb.hh>
#include "GoboRotator.hh"


extern "C" void lb_module_init(void)
{
  fprintf(stderr, "Initializing gobo rotators\n");

  GoboRotatorFactory* i_i = new GoboRotatorFactory();
  /* This pointer won't ever be freed */
  LB::InstrumentFactory_ptr i_ref = i_i->_this();
  lb->addDriver("gobo_rotator", i_ref);
  
  fprintf(stderr, "Done initializing gobo rotators\n");
}

GoboRotator::GoboRotator(const char *name, int dimmer_start) :
  LB_Instrument_i (name, dimmer_start)
{
  this->gobo_rpm_dimmer = this->level_dimmer;

  this->level_dimmer = NULL;
}

GoboRotator::~GoboRotator()
{
}

LB::AttrList* GoboRotator::getAttributes()
{
  LB::AttrList_var ret = new LB::AttrList;

  ret->length(1);
  ret[0]=LB::attr_gobo_rpm;
  return ret._retn();
}

void GoboRotator::setLevelFromSource(CORBA::Double level, 
					 const char* source)
{
}

void GoboRotator::updateLevelFromSources()
{
}

void GoboRotator::setLevel(CORBA::Double level)
{
}

void GoboRotator::setGoboRPM(CORBA::Double rpm)
{
  CORBA::Double val;

  this->my_gobo_rpm=rpm;

  // Let's see how they're controlled.
  // this->gobo_rpm_dimmer->setValue((long)((rpm/100.0)*255.0));

  if (this->gobo_rpm_listeners)
    {
      LB::Event evt;

      evt.source=this->_this();
      evt.value.length(1);
      evt.value[0]=rpm;
      evt.type=LB::event_instrument_gobo_rpm;

      lb->addEvent(evt);
    }
}

void GoboRotator::getGoboRPM(CORBA::Double& rpm)
{
  rpm = this->my_gobo_rpm;
}


/********** Factory stuff **********/

GoboRotatorFactory::GoboRotatorFactory()
{
}

GoboRotatorFactory::~GoboRotatorFactory()
{
}

LB::Instrument_ptr GoboRotatorFactory::createInstrument(const char* name, 
							const LB::ArgList& arguments)
{
  int dnum=0;

  for (int a=0; a<arguments.length(); a++)
    {
      if (strcmp(arguments[a].name, "dimmer") == 0)
	dnum = atoi(arguments[a].value);
    }

  GoboRotator* i_i = new GoboRotator(name, dnum);

  /* This pointer won't ever be freed */
  LB::Instrument_ptr i_ref = i_i->_this();
  return i_ref;
}
