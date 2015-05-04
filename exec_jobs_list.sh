#!/bin/bash

i=0
cat "jobs.list" | while read line
do
  echo "$line &> ./tests/job${i}.log &"
  eval "$line &> ./tests/job${i}.log &"
  i=$(( $i + 1 ))
  [[ $(( $i%10 )) -eq 0 ]] && wait
done
