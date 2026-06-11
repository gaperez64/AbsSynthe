# Test benchmarks

These small safety-AIGER games are a representative sample from the public
[SYNTCOMP](https://github.com/SYNTCOMP/benchmarks) benchmark set (CC-BY 4.0),
included here so the test suite is self-contained and exercises every solver
mode (default / abstraction `-a` / compositional `-c` / transition decomposition
`-t` / parallel `-p`) on realistic inputs:

- `mult2_real.aag`, `demo_real.aag` — realizable (`toy_examples`, `LTL2AIG`).
- `demo_unreal.aag` — unrealizable (`LTL2AIG`).
