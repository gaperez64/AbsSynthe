_buddy_wrap.so: buddy_wrap_wrap.cpp
	g++ -dynamiclib -Wl,-undefined,dynamic_lookup buddy_wrap_wrap.cpp \
		-fPIC -o _buddy_wrap.so \
		-I/usr/include/python2.7 -I/usr/local/include \
		-lpython2.7 -lbdd
buddy_wrap_wrap.cpp: buddy_wrap.i
	swig -I/usr/local/include -c++ -python -o buddy_wrap_wrap.cpp buddy_wrap.i
clean:
	rm _buddy_wrap.so buddy_wrap_wrap.c buddy_wrap.py
