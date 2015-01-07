
include ../../../common/arch.mk

CXX_FLAGS = -O3 -g

LD_FLAGS=-lm
ACC_LD_FLAGS=`ipmacc --ldflags`

ACC = ipmacc
ACC_FLAGS = -O3 $(ARCH)
ACL_FLAGS = -O3

# link objects(binaries) together
# #all:   main.o
#                         
#
#                         # compile main function file into object (binary)
#main.o: main.c define.c graphics.c

cpu:
	$(CXX) main.c -c $(CXX_FLAGS)      -o main_$(CXX).o
	g++ $(CXX_FLAGS) main_$(CXX).o $(LD_FLAGS)  -o srad_$(CXX)

cuda:
	$(ACC) main.c -c $(ACC_FLAGS) -o main_cuda.o
	g++ $(CXX_FLAGS) main_cuda.o   $(LD_FLAGS) $(ACC_LD_FLAGS) -o srad_cuda

opencl:
	ta=nvopencl $(ACC) main.c -c -O3 $(ACL_FLAGS) -o main_opencl.o
	g++ $(CXX_FLAGS) main_opencl.o $(LD_FLAGS) $(ACC_LD_FLAGS) -o srad_opencl

# delete all object files
clean:
	rm -f srad_* *.o  *_ipmacc.c* output*pgm

