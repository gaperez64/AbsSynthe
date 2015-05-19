CXX=clang++
CXXFLAGS=-Wall -std=c++11
HEADERS=abssynthe.h logging.h aig.h aiger.h
SOURCES=abssynthe.cpp logging.cpp aig.cpp aiger.c algos.cpp
CUDD_PATH=../swiss-abssynthe/cudd-2.5.1
CUDD_HDRS=$(CUDD_PATH)/include
CUDD_LIBS=$(CUDD_PATH)/obj/libobj.a \
	  $(CUDD_PATH)/cudd/libcudd.a \
	  $(CUDD_PATH)/mtr/libmtr.a \
	  $(CUDD_PATH)/st/libst.a \
	  $(CUDD_PATH)/util/libutil.a \
	  $(CUDD_PATH)/epd/libepd.a

abssynthe: $(HEADERS) $(SOURCES) $(CUDD_HDRS) $(CUDD_LIBS)
	$(CXX) $(CXXFLAGS) $(SOURCES) $(CUDD_LIBS) -o abssynthe -I $(CUDD_HDRS)
clean:
	rm -f abssynthe
switch_to_guillermo:
	git remote set-url origin https://github.com/gaperez64/abssynthe.git
	# we want to track origin/native-dev branch into our local swiss branch
	#git branch --set-upstream-to=origin/native-dev swiss
switch_to_osankur:
	git remote set-url origin https://github.com/osankur/abssynthe.git
