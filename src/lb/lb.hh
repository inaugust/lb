#ifndef __LB_HH__
#define __LB_HH__

#include <stdio.h>
#include <expat.h>
#include <glib.h>
#include "Lightboard.hh"
#include "attributes.hh"

#include <map.h>
struct ltstr
{
  bool operator()(const char* s1, const char* s2) const
  {
    return strcmp(s1, s2) < 0;
  }
};

extern LB::Lightboard_ptr lb;
extern CORBA::ORB_ptr orb;
extern CosNaming::NamingContext_ptr rootNaming;
extern CosNaming::NamingContext_ptr dimmerContext;

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


#endif __LB_HH__
