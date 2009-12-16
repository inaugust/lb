ACLOCAL_AMFLAGS = -I m4

IDLC=omniidl
IDL_ARGS=-Wba #-Wbuse_quotes

#AM_CPPFLAGS =  -O2 -g -D__OMNIORB4__ -D_REENTRANT  -D__x86__ -D__linux__ -D__OSVERSION__=2 `pkg-config --cflags glib-2.0` -I./lb
AM_CPPFLAGS=-isystem ${top_srcdir}/liblbidl -isystem ${top_builddir}/liblbidl  -I${top_srcdir}/lb -I${top_builddir}/lb `pkg-config --cflags glib-2.0`

#AM_LDFLAGS = -rdynamic -export-dynamic -ldl -lomniORB4  -lomniORB4 -lexpat -lpthread -lomniDynamic4 -lomnithread  `pkg-config --libs glib-2.0`
AM_LDFLAGS=`pkg-config --libs glib-2.0`

noinst_HEADERS= \
	lb/attributes.hh \
	lb/lb.hh \
	lb/CrossFader_i.hh \
	lb/CueFader_i.hh \
	lb/Dimmer_i.hh \
	lb/Fader_i.hh \
	lb/Instrument_i.hh \
	lb/LevelFader_i.hh \
	lb/Lightboard_i.hh \
	liblbidl/types.hh \
	liblbidl/CrossFader.hh \
	liblbidl/CueFader.hh \
	liblbidl/Dimmer.hh \
	liblbidl/Fader.hh \
	liblbidl/Instrument.hh \
	liblbidl/LevelFader.hh \
	liblbidl/Lightboard.hh

bin_PROGRAMS= lb/lb
noinst_LTLIBRARIES= lb/liblb.la liblbidl/liblbidl.la
moduledir=${libdir}/lb
module_LTLIBRARIES= lb/modules/GoboRotator.la

lb_lb_CXXFLAGS= ${AM_CXXFLAGS} -Wno-extra  ${NO_WERROR}
lb_lb_SOURCES= \
	lb/attributes.cc \
	lb/lb.cc
lb_lb_LDADD= lb/liblb.la liblbidl/liblbidl.la -lomniORB4 -ldl -lexpat

lb_liblb_la_CXXFLAGS= ${AM_CXXFLAGS} -Wno-extra ${NO_WERROR}
lb_liblb_la_SOURCES= \
	lb/CrossFader_i.cc \
	lb/CueFader_i.cc \
	lb/Dimmer_i.cc \
	lb/Fader_i.cc \
	lb/Instrument_i.cc \
	lb/LevelFader_i.cc \
	lb/Lightboard_i.cc

liblbidl_liblbidl_la_CXXFLAGS=${AM_CXXFLAGS} ${NO_WERROR}
liblbidl_liblbidl_la_SOURCES= \
	liblbidl/CrossFaderSK.cc \
	liblbidl/CrossFaderDynSK.cc \
	liblbidl/CueFaderSK.cc \
	liblbidl/CueFaderDynSK.cc \
	liblbidl/DimmerSK.cc \
	liblbidl/DimmerDynSK.cc \
	liblbidl/FaderSK.cc \
	liblbidl/FaderDynSK.cc \
	liblbidl/InstrumentSK.cc \
	liblbidl/InstrumentDynSK.cc \
	liblbidl/LevelFaderSK.cc \
	liblbidl/LevelFaderDynSK.cc \
	liblbidl/LightboardSK.cc \
	liblbidl/LightboardDynSK.cc \
	liblbidl/typesSK.cc \
	liblbidl/typesDynSK.cc


BUILT_PYTHON_FILES= \
	gtklb/idl/CrossFader_idl.py \
	gtklb/idl/CueFader_idl.py \
	gtklb/idl/Dimmer_idl.py \
	gtklb/idl/Fader_idl.py \
	gtklb/idl/Instrument_idl.py \
	gtklb/idl/LevelFader_idl.py \
	gtklb/idl/Lightboard_idl.py \
	gtklb/idl/types_idl.py

lb_modules_GoboRotator_la_SOURCES= lb/modules/GoboRotator.cc
lb_modules_GoboRotator_la_CXXFLAGS= ${AM_CXXFLAGS} ${NO_WERROR}
lb_modules_GoboRotator_la_LDFLAGS= -avoid-version -module -disable-static ${AM_LDFLAGS}
lb_modules_GoboRotator_la_LIBADD= liblbidl/liblbidl.la lb/liblb.la

#  module_LTLIBRARIES += lb/modules/MovingInstrument.la
#  lb_modules_MovingInstrument_la_SOURCES= lb/modules/MovingInstrument.cc
#  lb_modules_MovingInstrument_la_LDFLAGS= -avoid-version -module -disable-static ${AM_LDFLAGS}

BUILT_SOURCES= ${BUILT_PYTHON_FILES} \
	liblbidl/types.hh \
	liblbidl/CrossFader.hh \
	liblbidl/CueFader.hh \
	liblbidl/Dimmer.hh \
	liblbidl/Fader.hh \
	liblbidl/Instrument.hh \
	liblbidl/LevelFader.hh \
	liblbidl/Lightboard.hh


python_PYTHON= \
	${BUILT_PYTHON_FILES} \
	gtklb/*py

CLEANFILES=${liblbidl_liblbidl_la_SOURCES} ${BUILT_PYTHON_FILES}
clean-local:
	rm -rf gtklb/idl

liblbidl/%.hh liblbidl/%DynSK.cc liblbidl/%SK.cc: idl/%.idl 
	$(IDLC) -bcxx $(IDL_ARGS) -C liblbidl $<

gtklb/idl/%_idl.py: idl/%.idl
	$(IDLC) -bpython -Wbpackage=idl -C gtklb $<

lb/%_example.cc: idl/%.idl
	$(IDLC) $(IDL_ARGS) $(IDL_EXAMPLE_ARGS) -C lb $<
   
modules: idl
	$(MAKE) -C modules

modules-clean:
	$(MAKE) clean -C modules

modules-install:
	$(MAKE) install -C modules

.PHONY: modules modules-clean clean 
