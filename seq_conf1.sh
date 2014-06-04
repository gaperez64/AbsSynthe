DIR=`dirname $0`/
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${DIR}"binary/libcudd/":${DIR}"binary/aiger_swig"
# $1 contains the input filename (the name of the AIGER-file).
# $2 (if present) contains the output filename (your synthesis result, also in
#    AIGER format).
if [[ $# < 2 ]]; then
  COMMAND="python ${DIR}binary/synth.py $1"
  $COMMAND
  res=$?
else
  COMMAND="python ${DIR}binary/synth.py --out $2 $1"
  $COMMAND
  res=$?
  cat ${DIR}$2
fi
exit $res
