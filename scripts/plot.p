set term png size 600, 400 crop
set datafile separator ";"
set pointsize 2


set logscale y 10
set output "more30.png"
plot "< sort -n more30.csv -k2 -t ';'" using ($2) title 'classic' with lines,\
"< sort -n more30.csv -k3 -t ';'" using ($3) title 'comp. 1' with lines,\
"< sort -n more30.csv -k4 -t ';'" using ($4) title 'comp. 2' with lines,\
"< sort -n more30.csv -k5 -t ';'" using ($5) title 'comp. 3' with lines,\
"< sort -n more30.csv -k6 -t ';'" using ($6) title 'minimum' with lines

set logscale y 10
set output "load.png"
plot "< sort -n load.csv -k2 -t ';'" using ($2) title 'classic' with lines,\
"< sort -n load.csv -k3 -t ';'" using ($3) title 'comp. 1' with lines,\
"< sort -n load.csv -k4 -t ';'" using ($4) title 'comp. 2' with lines,\
"< sort -n load.csv -k5 -t ';'" using ($5) title 'comp. 3' with lines,\
"< sort -n load.csv -k6 -t ';'" using ($6) title 'minimum' with lines

set logscale y 10
set output "genbuf.png"
plot "< sort -n genbuf.csv -k2 -t ';'" using ($2) title 'classic' with lines,\
"< sort -n genbuf.csv -k3 -t ';'" using ($3) title 'comp. 1' with lines,\
"< sort -n genbuf.csv -k4 -t ';'" using ($4) title 'comp. 2' with lines,\
"< sort -n genbuf.csv -k5 -t ';'" using ($5) title 'comp. 3' with lines,\
"< sort -n genbuf.csv -k6 -t ';'" using ($6) title 'minimum' with lines

set logscale y 10
set output "amba.png"
plot "< sort -n amba.csv -k2 -t ';'" using ($2) title 'classic' with lines,\
"< sort -n amba.csv -k3 -t ';'" using ($3) title 'comp. 1' with lines,\
"< sort -n amba.csv -k4 -t ';'" using ($4) title 'comp. 2' with lines,\
"< sort -n amba.csv -k5 -t ';'" using ($5) title 'comp. 3' with lines,\
"< sort -n amba.csv -k6 -t ';'" using ($6) title 'minimum' with lines

quit
