#CXX = g++-3.0

CPPFLAGS =  -O2 -g -D__OMNIORB3__ -D_REENTRANT  -I. -I.. -D__x86__ -D__linux__ -D__OSVERSION__=2 `glib-config --cflags`

LDFLAGS = -rdynamic -export-dynamic -ldl -lomniORB3  -lomniGK_stub -lexpat -lpthread -lomniDynamic3 -lomnithread  `glib-config --libs`

IDLC=omniidl
IDL_ARGS=-bcxx -Wba #-Wbuse_quotes
IDL_EXAMPLE_ARGS=-Wbexample

#####################################
#
# Implementation files that don't have anything to do with IDL
#
IMPL_FILES = lb attributes

#
# Implementation files that are also IDL files
#
IMPL_IDL_FILES = Lightboard Instrument Fader CueFader CrossFader LevelFader\
	Dimmer

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

all: lb modules

lb : idl $(OBJECTS)
	$(CXX) -o lb $(LDFLAGS) $(OBJECTS) 

idl : $(IDL_H)

%.hh %DynSK.cc %SK.cc: ../../idl/%.idl
	$(IDLC) $(IDL_ARGS) $<

%_example.cc: ../../idl/%.idl
	$(IDLC) $(IDL_ARGS) $(IDL_EXAMPLE_ARGS) $<

clean: modules-clean
	rm -f $(OBJECTS) $(IDL_H) $(IDL_CC) lb *~
   
modules: idl
	$(MAKE) -C modules

modules-clean:
	$(MAKE) clean -C modules

modules-install:
	$(MAKE) install -C modules

.PHONY: modules modules-clean clean 
