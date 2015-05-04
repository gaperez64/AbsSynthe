#!/bin/bash

# This directory:
DIR=`dirname $0`/

# The directory where the benchmarks are located:
BM_DIR="\$HOME/bench-syntcomp14/"

REAL=10
UNREAL=20

# The benchmarks to be used.
# The files have to be located in ${BM_DIR}.

FILES=(
cycle_sched_10_2_1   $REAL
cycle_sched_10_2_2   $REAL
cycle_sched_11_2_1   $REAL
cycle_sched_12_2_1   $REAL
cycle_sched_12_2_2   $REAL
cycle_sched_12_2_3   $REAL
cycle_sched_12_2_4   $REAL
cycle_sched_13_2_1   $REAL
cycle_sched_14_2_1   $REAL
cycle_sched_14_2_2   $REAL
cycle_sched_15_2_1   $REAL
cycle_sched_15_2_3   $REAL
cycle_sched_16_2_1   $REAL
cycle_sched_16_2_2   $REAL
cycle_sched_16_2_4   $REAL
cycle_sched_17_2_1   $REAL
cycle_sched_18_2_1   $REAL
cycle_sched_18_2_3   $REAL
cycle_sched_19_2_1   $REAL
cycle_sched_20_2_4   $REAL
cycle_sched_21_2_3   $REAL
cycle_sched_24_2_3   $REAL
cycle_sched_24_2_4   $REAL
cycle_sched_28_2_4   $REAL
cycle_sched_2_2_1   $REAL
cycle_sched_32_2_4   $REAL
cycle_sched_3_2_1   $REAL
cycle_sched_4_2_1   $REAL
cycle_sched_4_2_2   $REAL
cycle_sched_5_2_1   $REAL
cycle_sched_6_2_1   $REAL
cycle_sched_6_2_2   $REAL
cycle_sched_6_2_3   $REAL
cycle_sched_7_2_1   $REAL
cycle_sched_8_2_1   $REAL
cycle_sched_8_2_2   $REAL
cycle_sched_8_2_4   $REAL
cycle_sched_9_2_1   $REAL
cycle_sched_9_2_3   $REAL
)

DECOMPABLE=(
cycle_sched_10_2_1
cycle_sched_10_2_2
cycle_sched_11_2_1
cycle_sched_12_2_1
cycle_sched_12_2_2
cycle_sched_12_2_3
cycle_sched_12_2_4
cycle_sched_13_2_1
cycle_sched_14_2_1
cycle_sched_14_2_2
cycle_sched_15_2_1
cycle_sched_15_2_3
cycle_sched_16_2_1
cycle_sched_16_2_2
cycle_sched_16_2_4
cycle_sched_17_2_1
cycle_sched_18_2_1
cycle_sched_18_2_3
cycle_sched_19_2_1
cycle_sched_20_2_4
cycle_sched_21_2_3
cycle_sched_24_2_3
cycle_sched_24_2_4
cycle_sched_28_2_4
cycle_sched_2_2_1
cycle_sched_32_2_4
cycle_sched_3_2_1
cycle_sched_4_2_1
cycle_sched_4_2_2
cycle_sched_5_2_1
cycle_sched_6_2_1
cycle_sched_6_2_2
cycle_sched_6_2_3
cycle_sched_7_2_1
cycle_sched_8_2_1
cycle_sched_8_2_2
cycle_sched_8_2_4
cycle_sched_9_2_1
cycle_sched_9_2_3
)

for element in $(seq 0 2 $((${#FILES[@]} - 1)))
do
     for de in $(seq 0 1 $((${#DECOMPABLE[@]} - 1)))
     do
     if [[ ${FILES[$element]} == ${DECOMPABLE[$de]} ]]; then
	     file_name=${FILES[$element]}
	     infile_path=${BM_DIR}${file_name}.aag
	     correct_real=${FILES[$element+1]}
		for solver in $(seq 0 1 4)
		do
			echo "\$HOME/AbsSynthe/start_co"$solver".sh" $infile_path $correct_real >> ${DIR}"jobs.list"
		done
     		break
     fi
     done
done
