#ifndef __LB_HH__
#define __LB_HH__

/*
  Files in the core should include this.  It defines the global variables,
  and includes all the generated idl stuff by way of Lightboard.hh.
  attributes.hh is also included, since in provides similar global functions.
  
  The cleanest way to do it is let the _i.hh file include this.
*/

#include <Lightboard.hh>
#include <attributes.hh>

extern LB::Lightboard_ptr lb;
extern CORBA::ORB_ptr orb;
extern CosNaming::NamingContext_ptr rootNaming;
extern CosNaming::NamingContext_ptr dimmerContext;

typedef struct 
{
  CORBA::Long id;
  LB::EventListener_ptr listener;
} ListenerRecord;
  

int make_level(const char *level);
double make_time(const char *t);
LB::Cue *duplicate_cue (const LB::Cue& incue, int zero);
void normalize_cues (const LB::Cue& incue1, const LB::Cue& incue2,
		     LB::Cue &outcue1, LB::Cue &outcue2);
CORBA::Boolean
bindObjectToName(CORBA::ORB_ptr orb, CORBA::Object_ptr objref, 
                 const char* id, const char* kind);
CORBA::Boolean
bindContextToName(CORBA::ORB_ptr orb, CORBA::Object_ptr objref, 
		  const char* id);
void 
recursive_unbind_and_destroy(CosNaming::NamingContext_ptr context, 
			     CosNaming::Name name);

#endif
