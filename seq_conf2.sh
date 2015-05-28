#!/bin/bash
DIR=`dirname $0`/
# $1 contains the input filename (the name of the AIGER-file).
# $2 (if present) contains the output filename (your synthesis result, also in
#    AIGER format).
if [[ $# < 2 ]]; then
    COMMAND="${DIR}binary/abssynthe -c 1 $1"
    $COMMAND
    if [[ $res == 10 ]]; then
        echo "REALIZABLE"
    else
        echo "UNREALIZABLE"
    fi
else
    COMMAND="${DIR}binary/abssynthe -c 1 $1 -o $2"
    $COMMAND
    res=$?
    if [[ $res == 10 ]]; then
        cat ${DIR}$2
    else
        echo "UNREALIZABLE"
    fi
fi
exit $res
