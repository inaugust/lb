CCFLAGS=-O2 -D__x86__ -D__linux__ -D__OSVERSION__=2 -I.
LDFLAGS=-lomniORB3 -lomniGK_stub
IDL=omniidl
IDLFLAGS=-bcxx -Wbuse_quotes
IDLPYFLAGS=-bpython
CC=g++
ECHO_FILES=echoSK.o echo_i.o

%.o : %.cc 
	$(CC) $(CCFLAGS) -c $<

echo: $(ECHO_FILES)
	$(CC) $(LDFLAGS) -o $@ $(ECHO_FILES)

echoSK.cc: echo.idl
	$(IDL) $(IDLFLAGS) echo.idl

echo-python:
	$(IDL) $(IDLPYFLAGS) echo.idl

clean:
	$(RM) -rf *.o echoSK.cc echo.hh echo Test Test__POA echo_idl.py* echo.ior echo.pid 
