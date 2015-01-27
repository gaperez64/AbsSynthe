_aiger_wrap.so: aiger_wrap_wrap.c aiger.c
	gcc -dynamiclib -Wl,-undefined,dynamic_lookup aiger_wrap_wrap.c \
		aiger.c \
		-fPIC -o _aiger_wrap.so \
		-I/usr/include/python2.7 \
		-lpython2.7
aiger_wrap_wrap.c: aiger_wrap.i aiger.h
	swig -python aiger_wrap.i
clean:
	rm _aiger_wrap.so aiger_wrap_wrap.c aiger_wrap.py
