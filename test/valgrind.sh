#!/bin/sh
# valgrind.sh PROG [ARGS...] -- passes iff valgrind reports no errors or definite
# leaks (CUDD keeps reachable memory at exit, so only 'definite' kinds count).
valgrind --error-exitcode=99 --leak-check=full --errors-for-leak-kinds=definite \
  -q "$@" >/dev/null 2>&1
[ "$?" = 99 ] && { echo "valgrind reported errors for: $*" >&2; exit 1; }
exit 0
