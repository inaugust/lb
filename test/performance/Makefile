CXXFLAGS = -O2 -D__x86__ -D__linux__ -D__OSVERSION__=2  -Wall
LDFLAGS = -lomniORB3 -lomniGK_stub
IDL=omniidl
IDLFLAGS=-bcxx -Wbuse_quotes
IDLPYFLAGS=-bpython

CC=g++
OBJS=echoSK.o echo_i.o
TARGETS=echo

echo: $(OBJS)
	$(CXX) $(LDFLAGS) -o $@ $(OBJS)

echoSK.cc: echo.idl
	$(IDL) $(IDLFLAGS) echo.idl

echo-python:
	$(IDL) $(IDLPYFLAGS) echo.idl

clean:
	$(RM) -rf *.o echoSK.cc echo.hh echo Test Test__POA echo_idl.py* echo.ior echo.pid 
