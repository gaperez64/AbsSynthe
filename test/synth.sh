#!/bin/sh
# synth.sh PROG GAME -- passes iff GAME is realizable and a non-empty strategy
# is written (exercises strategy extraction: synthAlgo / bdd2aig / finalizeSynth).
set -u
prog="$1"; game="$2"
strat="$(mktemp)"; trap 'rm -f "$strat"' EXIT
"$prog" -o "$strat" "$game" >/dev/null 2>&1
[ "$?" = 10 ] || { echo "$game: expected realizable (10)" >&2; exit 1; }
[ -s "$strat" ] || { echo "$game: empty strategy" >&2; exit 1; }
exit 0
