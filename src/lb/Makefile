#CXX = g++-3.0

CPPFLAGS =  -O2 -D__OMNIORB3__ -D_REENTRANT  -I/usr/local/include/omniORB3 -D__x86__ -D__linux__ -D__OSVERSION__=2 `glib-config --cflags`

#Older version
#CPPFLAGS = -D_REENTRANT -D__OMNIORB3__ -D__x86__ -D__linux__ -D__OSVERSION__=2 -I. -I/usr/include -I/usr/include/COS -I/usr/local/include/omniORB3

LDFLAGS = -lomniORB3  -lomniGK_stub -lexpat -lpthread -lomniDynamic3 -lomnithread -L/usr/local/lib/omniORB3 `glib-config --libs`

#

IDLC=omniidl
IDL_ARGS=-bcxx -Wbuse_quotes -Wba
IDL_EXAMPLE_ARGS=-Wbexample

#####################################
#
# Implementation files that don't have anything to do with IDL
#
IMPL_FILES = lb

#
# Implementation files that are also IDL files
#
IMPL_IDL_FILES = Lightboard Instrument Fader CueFader CrossFader LevelFader\
	MovingInstrument Dimmer

#
# IDL Files that don't have Implementation files
#
IDL_FILES = types

#######################################
#
# Don't edit below this point
#

OBJECTS := $(foreach file,$(IMPL_FILES),$(file).o) \
	$(foreach file,$(IMPL_IDL_FILES),$(file)_i.o $(file)SK.o $(file)DynSK.o) \
	$(foreach file,$(IDL_FILES),$(file)SK.o $(file)DynSK.o) \

IDL_H := $(foreach file,$(IMPL_IDL_FILES),$(file).hh) \
	$(foreach file,$(IDL_FILES),$(file).hh) 

IDL_CC := $(foreach file,$(IMPL_IDL_FILES),$(file)SK.cc $(file)DynSK.cc) \
	$(foreach file,$(IDL_FILES),$(file)SK.cc $(file)DynSK.cc)

all: lb

lb : idl $(OBJECTS)
	$(CXX) -o lb $(LDFLAGS) $(OBJECTS) 

idl : $(IDL_H)

%.hh %DynSK.cc %SK.cc: ../../idl/%.idl
	$(IDLC) $(IDL_ARGS) $<

%_example.cc: ../../idl/%.idl
	$(IDLC) $(IDL_ARGS) $(IDL_EXAMPLE_ARGS) $<

clean:
	rm -f $(OBJECTS) $(IDL_H) $(IDL_CC) lb *~

