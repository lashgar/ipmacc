
include ../../common/arch.mk

DUMPOUT= -DDUMPOUT

CC = g++
CC_FLAGS  =  $(DUMPOUT)

ACC = ipmacc
ACC_FLAGS =  $(ARCH) $(DUMPOUT)
ACL_FLAGS =  $(DUMPOUT)

SRC = pathfinder.cpp
EXE = pathfinder

cpu:
	$(CC)  $(SRC) $(CC_FLAGS)  -o $(EXE)_$(CC)
cuda:
	$(ACC) $(SRC) $(ACC_FLAGS) -o $(EXE)_cuda
opencl:
	ta=nvopencl $(ACC) $(SRC) $(ACL_FLAGS) -o $(EXE)_ocl

clean:
	rm -f pathfinder_* _ipmacc* *txt *log
