#ifndef __LB_HH__
#define __LB_HH__

#include <stdio.h>
#include <expat.h>
#include "Lightboard.hh"
#include <CosEventChannelAdmin.hh>

#include <map.h>
struct ltstr
{
  bool operator()(const char* s1, const char* s2) const
  {
    return strcmp(s1, s2) < 0;
  }
};

extern LB::Lightboard_ptr lb;
extern CosEventChannelAdmin::ProxyPushConsumer_ptr proxy_consumer;

int make_level(const char *level);
double make_time(const char *t);

#endif __LB_HH__
