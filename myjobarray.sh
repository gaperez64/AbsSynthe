#!/bin/bash -l

#PBS -t 1-2696
#PBS -l nodes=1:ppn=1
#PBS -l walltime=01:23:20
#PBS -l mem=60gb
#PBS -N SyntCompArray
#PBS -o bench${PBS_ARRAYID}.out
#PBS -j oe
#PBS -m abe

# Execute the line matching the array index from file one_command_per_index.list:
cmd=`head -${PBS_ARRAYID} $HOME"/AbsSynthe/jobs.list" | tail -1`

# Execute the command extracted from the file:
eval $cmd
