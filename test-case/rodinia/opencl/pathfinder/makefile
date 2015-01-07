include ../../common/make.config
CXX = g++ -DDUMPOUT
DEBUGFLAGS = -g
# You will need to modify the following 2 lines
# by inserting the correct path to the OpenCL
# lib and inc directories.
CXXFLAGS = -I$(OPENCLINC) -c $(DEBUGFLAGS)
LINKFLAGS = -L$(OPENCLLIB) -lOpenCL

# link objects(binaries) together
a.out: main.o OpenCL.o
	$(CXX) $(LINKFLAGS) main.o OpenCL.o -o pathfinder

# compile main function file into object (binary)
main.o: main.cpp OpenCL.cpp kernels.cl
	$(CXX) $(CXXFLAGS) main.cpp OpenCL.cpp

clean:
	rm -f pathfinder *.o *.out *~ *\#
