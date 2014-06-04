_aiger_wrap.so: aiger_wrap_wrap.c aiger.c
	gcc -shared aiger_wrap_wrap.c \
		aiger.c \
		-fPIC -o _aiger_wrap.so \
		-I/usr/include/python2.6
aiger_wrap_wrap.c: aiger_wrap.i
	swig -python aiger_wrap.i
