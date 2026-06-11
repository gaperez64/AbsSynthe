#!/bin/sh
# Build the vendored CUDD 2.5.1 and copy its static archives to the meson out
# dir.  Idempotent: extracts the tarball and runs CUDD's own `make objlib` only
# when needed (CUDD 2.5.1 keeps its own legacy build system; we do not port it).
#
#   build-cudd.sh SOURCE_DIR OUT_DIR
# SOURCE_DIR holds cudd-2.5.1.tar.gz; the archives are copied into OUT_DIR.
set -eu

src_dir="$1"
out_dir="$2"
cudd="$src_dir/cudd-2.5.1"

if [ ! -d "$cudd" ]; then
  (cd "$src_dir" && tar -zxf cudd-2.5.1.tar.gz)
fi
if [ ! -f "$cudd/cudd/libcudd.a" ]; then
  make -C "$cudd" objlib >/dev/null
fi

# Link order matters for these static archives (mirrors source/Makefile).
for a in obj/libobj cudd/libcudd mtr/libmtr st/libst util/libutil epd/libepd; do
  cp "$cudd/$a.a" "$out_dir/$(basename "$a.a")"
done
