project('abssynthe', 'c', 'cpp',
  version: '2.1',
  meson_version: '>=0.60',
  default_options: [
    'cpp_std=c++11',
    'optimization=3',
    'b_ndebug=if-release',
    'warning_level=1',
  ])

src = meson.current_source_dir() / 'source'
cudd = src / 'cudd-2.5.1'

# CUDD 2.5.1 is vendored as a tarball with its own legacy build system; we do not
# port it.  Build it in place at configure time (extract + its own `make
# objlib`, which assembles its include/ dir and static archives).  build-cudd.sh
# is idempotent, so reconfigures are cheap.
run_command(files('build-cudd.sh'), src, check: true)

cudd_dep = declare_dependency(
  include_directories: include_directories('source/cudd-2.5.1/include'),
  # Link order mirrors source/Makefile.
  link_args: [
    cudd / 'obj/libobj.a', cudd / 'cudd/libcudd.a', cudd / 'mtr/libmtr.a',
    cudd / 'st/libst.a', cudd / 'util/libutil.a', cudd / 'epd/libepd.a', '-lm',
  ])

threads = dependency('threads')

# AbsSynthe-authored C++ plus the vendored Biere aiger.c/aigtocnf.c (compiled as
# C).  The Biere files and CUDD are excluded from clang-format/clang-tidy.
abssynthe = executable('abssynthe',
  files('source/abssynthe.cpp', 'source/logging.cpp', 'source/aig.cpp',
        'source/aiger.c', 'source/aigtocnf.c', 'source/algos.cpp'),
  dependencies: [cudd_dep, threads],
  install: false)

subdir('test')
