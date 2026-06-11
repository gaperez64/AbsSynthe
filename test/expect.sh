#!/bin/sh
# expect.sh EXPECTED_EXIT PROG [ARGS...] -- passes iff PROG exits EXPECTED_EXIT.
set -u
expected="$1"; shift
"$@" >/dev/null 2>&1
got=$?
[ "$got" = "$expected" ] && exit 0
echo "expected exit $expected, got $got: $*" >&2
exit 1
