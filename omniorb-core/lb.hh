#ifndef __LB_HH__
#define __LB_HH__

#include <map.h>
struct ltstr
{
  bool operator()(const char* s1, const char* s2) const
  {
    return strcmp(s1, s2) < 0;
  }
};

#endif __LB_HH__
