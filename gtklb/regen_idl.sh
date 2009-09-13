#!/bin/sh

cd ../../lib/python/
omniidl -bpython -Wbpackage=idl ../../idl/*.idl
cd ../../src/gtklb/

