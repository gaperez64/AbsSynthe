#!/bin/bash
# change python version
PYVER="python2.6"
mkdir ./binary
# python scripts
cp ./code/*.py ./binary
# aiger_swig
cd ./code/aiger_swig
sed -i "s/python2.7/${PYVER}/g" Makefile
make
cd ../..
mkdir ./binary/aiger_swig
cp ./code/aiger_swig/*.py ./code/aiger_swig/*.so ./binary/aiger_swig
# pycudd
tar -xvf ./code/pycudd2.0.2.tar.gz
cd ./pycudd2.0.2/cudd-2.4.2
# x86_64 specific
sed -i "s/\(^XCFLAGS\.*\)/#\1/g" Makefile
sed -i "1iXCFLAGS	= -mtune=native -DHAVE_IEEE_754 -DBSD -DSIZEOF_VOID_P=8 -DSIZEOF_LONG=8 -fPIC" Makefile
make
make libso
cd ../pycudd
sed -i "s/python2.7/${PYVER}/g" Makefile
make
cd ../..
cp ./pycudd2.0.2/pycudd/pycudd.py ./binary/pycudd.py
cp ./pycudd2.0.2/pycudd/_pycudd.so ./binary/_pycudd.so
mkdir ./binary/libcudd
cp ./pycudd2.0.2/cudd-2.4.2/lib/*.so ./binary/libcudd
