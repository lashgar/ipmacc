
include ../../common/arch.mk

CC = g++
CC_FLAGS  = -g 

ACC = ipmacc
ACC_FLAGS = -g $(ARCH)
ACL_FLAGS = -g 

SRC = pathfinder.cpp
EXE = pathfinder

cpu:
	$(CC)  $(SRC) $(CC_FLAGS)  -o $(EXE)_$(CC)
cuda:
	$(ACC) $(SRC) $(ACC_FLAGS) -o $(EXE)_cuda
opencl:
	ta=nvopencl $(ACC) $(SRC) $(ACL_FLAGS) -o $(EXE)_opencl

clean:
	rm -f pathfinder_* _ipmacc.c* output*txt
