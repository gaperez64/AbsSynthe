DIR=`dirname $0`/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${DIR}"binary/libcudd/":${DIR}"binary/aiger_swig"
# $1 contains the input filename (the name of the AIGER-file).
# $2 (if present) contains the output filename (your synthesis result, also in
#    AIGER format).
if [[ $# < 2 ]]; then
  COMMAND1="python ${DIR}binary/synth.py $1"
  COMMAND2="python ${DIR}binary/synth.py -a -i 4 -l 2 $1"
else
  COMMAND1="python ${DIR}binary/synth.py --out $2 $1"
  COMMAND2="python ${DIR}binary/synth.py -a -i 4 -l 2 --out $2 $1"
fi
ulimit -t 2500
$COMMAND1
res=$?
if [[ ${res} != 10 && ${res} != 20 ]]; then
  echo "Timed out with concrete algo, launching abstract one..."
  echo $COMMAND2
  $COMMAND2
  res=$?
fi
if [[ $# = 2 ]]; then
  cat ${DIR}$2
fi
exit $res
