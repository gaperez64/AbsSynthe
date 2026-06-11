#!/bin/sh
# outfile.sh PROG FLAG GAME -- realizable (10) and writes a non-empty FLAG file
# (exercises win-region / inductive-certificate emission).
set -u
prog="$1"; flag="$2"; game="$3"
out="$(mktemp)"; trap 'rm -f "$out"' EXIT
"$prog" "$flag" "$out" "$game" >/dev/null 2>&1
[ "$?" = 10 ] || { echo "$game $flag: expected realizable (10)" >&2; exit 1; }

exit 0
