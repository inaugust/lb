#!/bin/sh
./echo >echo.ior 2>&1 &
echo $! > echo.pid
export PYTHONPATH=/usr/lib:$PYTHONPATH
sleep 1
echo "omniORB Test"
./test-omni `cat echo.ior`
echo "ORBit Test"
./test-orbit `cat echo.ior`

kill `cat echo.pid`
rm echo.pid echo.ior

