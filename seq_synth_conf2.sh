#!/bin/bash
DIR=`dirname $0`/
# $1 contains the input filename (the name of the AIGER-file).
COMMAND="${DIR}binary/abssynthe -a $1 -o $1-result.aag"
$COMMAND
res=$?
if [[ $res == 10 ]]; then
    cat "$1-result.aag"
else
    echo "UNREALIZABLE"
fi
exit $res
