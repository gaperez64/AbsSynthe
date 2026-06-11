#!/bin/sh
# Build the vendored CUDD 2.5.1 in place (extract the tarball + run CUDD's own
# legacy `make objlib`, which also assembles its include/ directory).  Idempotent
# so meson can call it on every (re)configure cheaply.  We do not port CUDD's
# build system.
#
#   build-cudd.sh SOURCE_DIR        (SOURCE_DIR holds cudd-2.5.1.tar.gz)
set -eu

src_dir="$1"
cudd="$src_dir/cudd-2.5.1"

if [ ! -d "$cudd" ]; then
  (cd "$src_dir" && tar -zxf cudd-2.5.1.tar.gz)
fi
if [ ! -f "$cudd/cudd/libcudd.a" ] || [ ! -d "$cudd/include" ]; then
  make -C "$cudd" objlib >/dev/null
fi
