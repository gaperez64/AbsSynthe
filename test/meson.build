expect = find_program('expect.sh')
synth = find_program('synth.sh')
outfile = find_program('outfile.sh')

real = files('realizable.aag')
unreal = files('unrealizable.aag')

# Minimal hand-written games: verdicts, strategy extraction, win-region /
# inductive-certificate emission.
test('realizable', expect, args: ['10', abssynthe, real])
test('unrealizable', expect, args: ['20', abssynthe, unreal])
test('synthesize', synth, args: [abssynthe, real])

# Real SYNTCOMP safety benchmarks across every solver mode so abstraction,
# transition decomposition, the compositional algorithms and the parallel
# solver are all exercised on realistic inputs.
b_real = files('benchmarks/mult2_real.aag')
b_real2 = files('benchmarks/demo_real.aag')
b_unreal = files('benchmarks/demo_unreal.aag')

modes = {
  'default': [],
  'abstraction': ['-a'],
  'comp1': ['-c', '1'],
  'comp2': ['-c', '2'],
  'comp3': ['-c', '3'],
  'comp4': ['-c', '4'],
  'trans': ['-t'],
  'parallel': ['-p'],
}
foreach name, m : modes
  test('bench_real_' + name, expect, args: ['10', abssynthe] + m + [b_real])
endforeach
test('bench_real2', expect, args: ['10', abssynthe, b_real2])
test('bench_real2_abstraction', expect, args: ['10', abssynthe, '-a', b_real2])

# Larger realizable games with non-trivial strategies: exercise abstraction and
# strategy construction (copyGateFrom) on richer inputs.
b_add4n = files('benchmarks/add4n_real.aag')
b_cnt = files('benchmarks/cnt10y_real.aag')
test('bench_synth_add4n', synth, args: [abssynthe, b_add4n])
test('bench_abs_add4n', expect, args: ['10', abssynthe, '-a', b_add4n])
test('bench_comp_add4n', expect, args: ['10', abssynthe, '-c', '2', b_add4n])
test('bench_synth_cnt', synth, args: [abssynthe, b_cnt])
test('bench_abs_cnt', expect, args: ['10', abssynthe, '-a', b_cnt])
test('bench_comp_cnt', expect, args: ['10', abssynthe, '-c', '2', b_cnt])

# Unrealizable across the main modes.
test('bench_unreal', expect, args: ['20', abssynthe, b_unreal])
test('bench_unreal_abstraction', expect, args: ['20', abssynthe, '-a', b_unreal])
test('bench_unreal_comp', expect, args: ['20', abssynthe, '-c', '1', b_unreal])
test('bench_unreal_trans', expect, args: ['20', abssynthe, '-t', b_unreal])

# Strategy extraction + winning-region / inductive-certificate on a real game.
test('synthesize_bench', synth, args: [abssynthe, b_real])
test('win_region', outfile, args: [abssynthe, '-w', b_real])
test('ind_cert', outfile, args: [abssynthe, '-i', b_real])

# CLI / logging / ordering / rsynth paths.
test('help', expect, args: ['0', abssynthe, '--help'])
test('verbose', expect, args: ['10', abssynthe, '-v', '1', b_real])
test('rsynth', expect, args: ['10', abssynthe, '-r', b_real])
test('min_ordering', expect, args: ['10', abssynthe, '-m', b_real])
test('strat_ordering', expect, args: ['10', abssynthe, '-s', b_real])

# Memory check on the synthesis path (definite leaks / invalid accesses only).
valgrind_prog = find_program('valgrind', required: false)
if valgrind_prog.found()
  valgrind = find_program('valgrind.sh')
  test('valgrind_solve', valgrind, args: [abssynthe, b_real2], timeout: 120)
  test('valgrind_synth', valgrind, args: [abssynthe, '-o', '/dev/null', b_real],
       timeout: 120)
endif
