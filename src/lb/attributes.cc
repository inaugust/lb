#include "attributes.hh"

void get_attribute_value(LB::AttrValue &data, LB::Instrument_ptr ins)
{
  switch (data.attr)
    {
    case LB::attr_level:
      data.value.length(1);
      data.value[0] = ins->getLevel();
      break;
    case LB::attr_target:
      data.value.length(3);
      ins->getTarget(data.value[0], data.value[1], data.value[2]);
      break;
    }
}

void set_attribute_value(LB::AttrValue &data, LB::Instrument_ptr ins)
{
  switch (data.attr)
    {
    case LB::attr_level:
      ins->setLevel(data.value[0]);
      break;
    case LB::attr_target:
      ins->setTarget(data.value[0], data.value[1], data.value[2]);
      break;
    }
}

void interpolate_attribute_values(LB::AttrValue &start, LB::AttrValue &end,
				   double ratio, LB::AttrValue &out)
{
  out.attr = end.attr;
  switch (end.attr)
    {
    case LB::attr_level:
      out.value.length(1);
      out.value[0]=start.value[0]+((end.value[0]-start.value[0])*ratio);
      break;
    case LB::attr_target:
      out.value.length(3);
      out.value[0]=(end.value[0]-start.value[0])*ratio;
      out.value[1]=(end.value[1]-start.value[1])*ratio;
      out.value[2]=(end.value[2]-start.value[2])*ratio;
      break;
    }
}

