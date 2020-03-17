#!/bin/bash
DIR=`dirname $0`/
# $1 contains the input filename (the name of the AIGER-file).
COMMAND="${DIR}binary/abssynthe -a -c 1 -f 3 $1"
$COMMAND
res=$?
if [[ $res == 10 ]]; then
    echo "REALIZABLE"
else
    echo "UNREALIZABLE"
fi
exit $res
