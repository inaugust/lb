#ifndef __ATTRIBUTES_HH__
#define __ATTRIBUTES_HH__

#include <lb.hh>

void get_attribute_value(LB::AttrValue& data, LB::Instrument_ptr ins);
void set_attribute_value(LB::AttrValue& data, LB::Instrument_ptr ins);
void interpolate_attribute_values(LB::AttrValue& start,
                                  LB::AttrValue& end,
                                  double ratio,
                                  LB::AttrValue& out);


#endif
