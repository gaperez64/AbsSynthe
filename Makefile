CXX=g++
CXXFLAGS=-Wall
HEADERS=abssynthe.h logging.h aig.h aiger.h
SOURCES=abssynthe.cpp logging.cpp aig.cpp aiger.c

abssynthe: $(HEADERS) $(SOURCES)
	$(CXX) $(CXXFLAGS) $(SOURCES) -o abssynthe
clean:
	rm -f abssynthe
