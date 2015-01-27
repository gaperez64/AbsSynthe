#!/bin/bash
sort -t';' comp0.csv > sc0.csv
sort -t';' comp1.csv > sc1.csv
sort -t';' comp2.csv > sc2.csv
sort -t';' comp3.csv > sc3.csv

join -t';' sc0.csv sc1.csv > temp0.csv
join -t';' temp0.csv sc2.csv > temp1.csv
join -t';' temp1.csv sc3.csv > temp2.csv

awk -F';' '{m=$2;for(i=2;i<=NF;i++){if($i<m)m=$i;}print $1";"$2";"$3";"$4";"$5";"m}' temp2.csv > all.csv

grep -i 'amba*' all.csv > amba.csv
grep -i 'load*' all.csv > load.csv
grep -i 'gb_*' all.csv > genbuf.csv
awk -F';' '{if($6>30)print $1";"$2";"$3";"$4";"$5";"$6}' all.csv > more30.csv
