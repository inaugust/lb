#!/bin/sh

# This is a generic script for firing up a server, waiting for it to write
# its stringified IOR to a file, then firing up a server

if ! test -f ./test-suite.idl; then cp $srcdir/test-suite.idl .; fi

[ "x$srcdir" == "x" ] && srcdir=.

$srcdir/test-server&

until test -f ./test-server.ior; do sleep 1; done

if $srcdir/test-client; then
	kill $!
#	rm ./test-server.ior
else
	kill $!
#	rm ./test-server.ior
	exit 1
fi
