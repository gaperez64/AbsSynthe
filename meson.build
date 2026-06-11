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

# CUDD 2.5.1 is vendored as a tarball with its own legacy build system; we do not
# port it.  Extract it at configure time so its headers exist for
# include_directories(), then build its static archives with a custom target.
run_command('sh', '-c',
  '[ -d "@0@/cudd-2.5.1" ] || tar -zxf "@0@/cudd-2.5.1.tar.gz" -C "@0@"'.format(src),
  check: true)

cudd_inc = include_directories('source/cudd-2.5.1/include')
cudd_archives = ['libobj.a', 'libcudd.a', 'libmtr.a', 'libst.a', 'libutil.a',
                 'libepd.a']
cudd = custom_target('cudd',
  output: cudd_archives,
  command: [files('build-cudd.sh'), src, '@OUTDIR@'],
  build_by_default: true)

cudd_link = []
foreach a : cudd_archives
  cudd_link += meson.current_build_dir() / a
endforeach
cudd_dep = declare_dependency(
  sources: cudd, # build-order dependency on the custom target
  include_directories: cudd_inc,
  link_args: cudd_link + ['-lm'])

threads = dependency('threads')

# AbsSynthe-authored C++ plus the vendored Biere aiger.c/aigtocnf.c (compiled as
# C).  The Biere files and CUDD are excluded from clang-format/clang-tidy.
abssynthe = executable('abssynthe',
  files('source/abssynthe.cpp', 'source/logging.cpp', 'source/aig.cpp',
        'source/aiger.c', 'source/aigtocnf.c', 'source/algos.cpp'),
  dependencies: [cudd_dep, threads],
  install: false)

subdir('test')
