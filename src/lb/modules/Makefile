# For completeness, and easier reference, this is a superset of the makefile
# in ..

#CXX = g++-3.0

CPPFLAGS =  -O2 -g -D__OMNIORB3__ -D_REENTRANT  -I/usr/local/include/omniORB3 -I. -I.. -D__x86__ -D__linux__ -D__OSVERSION__=2 `glib-config --cflags`

LDFLAGS = -lomniORB3  -lomniGK_stub -lexpat -lpthread -lomniDynamic3 -lomnithread -L/usr/local/lib/omniORB3 `glib-config --libs`

IDLC=omniidl
IDL_ARGS=-bcxx -Wbuse_quotes -Wba
IDL_EXAMPLE_ARGS=-Wbexample

#####################################
#
# Implementation files that don't have anything to do with IDL
#
IMPL_FILES = 

#
# Implementation files that are also IDL files
#
IMPL_IDL_FILES = 

#
# IDL Files that don't have Implementation files
#
IDL_FILES = 

#
# Loadable Modules
#
MODULES = GoboRotator

#######################################
#
# Don't edit below this point
#

OBJECTS := $(foreach file,$(IMPL_FILES),$(file).o) \
	$(foreach file,$(IMPL_IDL_FILES),$(file)_i.o $(file)SK.o $(file)DynSK.o) \
	$(foreach file,$(IDL_FILES),$(file)SK.o $(file)DynSK.o)

IDL_H := $(foreach file,$(IMPL_IDL_FILES),$(file).hh) \
	$(foreach file,$(IDL_FILES),$(file).hh) 

IDL_CC := $(foreach file,$(IMPL_IDL_FILES),$(file)SK.cc $(file)DynSK.cc) \
	$(foreach file,$(IDL_FILES),$(file)SK.cc $(file)DynSK.cc)

LIB_OBJECTS := $(foreach file,$(MODULES),$(file).lo)

LIB_ARCHIVES := $(foreach file,$(MODULES),$(file).la)

NODEP_OBJECTS := $(foreach file,$(MODULES),$(file).o .libs/$(file).o)

all: modules # lb

modules: $(LIB_ARCHIVES)

install: $(LIB_ARCHIVES)
	libtool --mode=install install -c $< /usr/local/lib/lb/$<

.PHONY: install

%.la: %.lo
	libtool --mode=link g++ -module -rpath /usr/local/lib/lb $(LDFLAGS) $< -o $*.la

%.lo: %.cc
	libtool --mode=compile g++ $(CPPFLAGS) -c $<

lb : idl $(OBJECTS)
	$(CXX) -o lb $(LDFLAGS) $(OBJECTS) 

idl : $(IDL_H)

%.hh %DynSK.cc %SK.cc: ../../idl/%.idl
	$(IDLC) $(IDL_ARGS) $<

%_example.cc: ../../idl/%.idl
	$(IDLC) $(IDL_ARGS) $(IDL_EXAMPLE_ARGS) $<

clean:
	rm -f $(OBJECTS) $(IDL_H) $(IDL_CC) $(NODEP_OBJECTS) lb *~
	libtool --mode=clean rm -f $(LIB_ARCHIVES) $(LIB_OBJECTS)

