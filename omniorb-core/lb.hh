#ifndef __LB_HH__
#define __LB_HH__

#include <stdio.h>
#include <expat.h>
#include <glib.h>
#include "Lightboard.hh"

#include <map.h>
struct ltstr
{
  bool operator()(const char* s1, const char* s2) const
  {
    return strcmp(s1, s2) < 0;
  }
};

extern LB::Lightboard_ptr lb;
extern CORBA::ORB_var orb;

int make_level(const char *level);
double make_time(const char *t);
LB::Cue *duplicate_cue (const LB::Cue& incue, int zero);
void normalize_cues (const LB::Cue& incue1, const LB::Cue& incue2,
		     LB::Cue &outcue1, LB::Cue &outcue2);

#endif __LB_HH__
