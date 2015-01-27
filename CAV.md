AbsSynthe installation:
1. enter the aiger_swig folder and make (the Makefile can be run
   on a Mac by replacing Makefile by Makefile.llvm)
   NOTE: this step requires you have installed swig
2. untar pycudd, enter the cudd subfolder and
   2.1 make
   2.2 make libso
3. enter the pycudd subfolder and make
4. abssynthe is now ready to use

Test suite:
1. fetch the benchmarks from https://github.com/gaperez64/bench-syntcomp14 
   into ../bench-syntcomp14/
2. run ./test_real.sh to process all benchmarks with the classic algorithm
   a log (.txt) file will be generated in a subfolder tests
3. run ./test_real.sh -d 1 -ca 1 to process all benchmarks with algorithm 1
4. run ./test_real.sh -d 1 -ca 2 to process all benchmarks with algorithm 2
5. run ./test_real.sh -d 1 -ca 3 to process all benchmarks with algorithm 3

To generate the graphs included in the paper:
1. Use log_to_table.py to process the text files (all 4 of them) into comp0.csv,
   comp1.csv, comp2.csv and comp3.csv respectively
2. run the gen4csv.sh script
3. run gnuplot script plot.p
