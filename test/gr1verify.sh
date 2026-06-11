#!/bin/sh
# gr1verify.sh PROG GAME -- end-to-end GR(1) strategy check.
#
# 1. Synthesize a controller for GAME (-o); it must be realizable (10) and a
#    non-empty strategy must be written.
# 2. Model-check the controller by re-solving it: finalizeSynth turns the
#    controllable inputs into gates, leaving a closed system whose only inputs
#    are the environment's, so the GR(1) controllable predecessor degenerates to
#    "for all environments".  The solver then accepts (10) iff the controller
#    enforces the justice/fairness winning condition against every environment.
#    A wrong strategy makes the closed system lose and the re-solve returns 20.
set -u
prog="$1"; game="$2"
ctrl="$(mktemp)"; trap 'rm -f "$ctrl"' EXIT

"$prog" -o "$ctrl" "$game" >/dev/null 2>&1
[ "$?" = 10 ] || { echo "$game: expected realizable (10)" >&2; exit 1; }
[ -s "$ctrl" ] || { echo "$game: empty strategy" >&2; exit 1; }

"$prog" "$ctrl" >/dev/null 2>&1
[ "$?" = 10 ] || { echo "$game: synthesized controller fails model-check" >&2; exit 1; }
exit 0
