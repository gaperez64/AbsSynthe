DIR=`dirname $0`/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${DIR}"binary/libcudd/":${DIR}"binary/aiger_swig"
# $1 contains the input filename (the name of the AIGER-file).
# $2 (if present) contains the output filename (your synthesis result, also in
#    AIGER format).
if [[ $# < 2 ]]; then
  COMMAND1="python ${DIR}binary/synth.py $1"
  COMMAND2="python ${DIR}binary/synth.py $1 -rc"
  COMMAND3="python ${DIR}binary/synth.py -a -i 4 -l 2 $1"
else
  COMMAND1="python ${DIR}binary/synth.py --out $2 $1"
  COMMAND2="python ${DIR}binary/synth.py --out $2 $1 -rc"
  COMMAND3="python ${DIR}binary/synth.py -a -i 4 -l 2 --out $2 $1"
fi

$COMMAND1 &
pid1=$!
$COMMAND2 &
pid2=$!
$COMMAND3 &
pid3=$!

while :; do
  if kill -0 $pid1 2>/dev/null; then
    :
  else
    wait $pid1
    res=$?
    kill $pid2 2>/dev/null
    kill $pid3 2>/dev/null
    break
  fi
  if kill -0 $pid2 2>/dev/null; then
    :
  else
    wait $pid2
    res=$?
    kill $pid1 2>/dev/null
    kill $pid3 2>/dev/null
    break
  fi
  if kill -0 $pid3 2>/dev/null; then
    :
  else
    wait $pid3
    res=$?
    kill $pid1 2>/dev/null
    kill $pid2 2>/dev/null
    break
  fi
  # sleep 5 seconds before re-polling
  sleep 5
done

if [[ $# = 2 ]]; then
  cat ${DIR}$2
fi
exit $res
