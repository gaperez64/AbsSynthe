#!/bin/bash
DIR=`dirname $0`/
cd ${DIR}source
tar -zxvf cudd-2.5.1.tar.gz
cd ${DIR}source/cudd-2.5.1
make objlib
cd ${DIR}source
make
cd ${DIR}
mkdir ${DIR}binary
cp ${DIR}source/abssynthe ${DIR}binary/abssynthe
