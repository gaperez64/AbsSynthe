#!/bin/bash
DIR=`dirname $0`/
# $1 contains the input filename (the name of the AIGER-file).
COMMAND="${DIR}binary/abssynthe -a $1 -o $1-result.aag -w $1-wregion.aag"
$COMMAND
res=$?
if [[ $res == 10 ]]; then
    echo "REALIZABLE"
    cat "$1-result.aag"
    echo "WINNING_REGION"
    cat "$1-wregion.aag"
else
    echo "UNREALIZABLE"
fi
exit $res
