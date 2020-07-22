#!/bin/bash
DIR=`dirname $0`/
cd ${DIR}source
tar -zxvf cudd-2.5.1.tar.gz
cd cudd-2.5.1
make objlib
cd ..
make abssynthe
cd ..
mkdir -p ${DIR}binary
cp ${DIR}source/abssynthe ${DIR}binary/abssynthe
