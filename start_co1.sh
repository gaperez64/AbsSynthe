#!/bin/bash

prog=$HOME"/AbsSynthe/abssynthe.py"
REAL=10
UNREAL=20

# SIMPLE script to set variables before playing with python version of AbsSynthe
PYTHONPATH=$HOME"/AbsSynthe/pycudd2.0.2/pycudd":$PYTHONPATH LD_LIBRARY_PATH=$HOME"/AbsSynthe/pycudd2.0.2/cudd-2.4.2/lib":$LD_LIBRARY_PATH python $prog $1 -v L -d 1 -ca 1
exit_code=$?
correct_real=$2

# BEGIN analyze realizability verdict
if [[ $exit_code == $REAL && $correct_real == $UNREAL ]];
then
 echo "ERROR: Tool reported 'realizable' for an unrealizable spec!!!!!!!!!!!!!!!!!!!!!!!!!!!"
 echo "Realizability correct: 0 (tool reported 'realizable' instead of 'unrealizable')" 1>&2
fi
if [[ $exit_code == $UNREAL && $correct_real == $REAL ]];
then
 echo "ERROR: Tool reported 'unrealizable' for a realizable spec!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
 echo "Realizability correct: 0 (tool reported 'unrealizable' instead of 'realizable')" 1>&2
fi
