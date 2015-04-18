abssynthe: abssynthe.h abssynthe.cpp logging.cpp logging.h
	g++ abssynthe.cpp logging.cpp -o abssynthe
clean:
	rm -f abssynthe
