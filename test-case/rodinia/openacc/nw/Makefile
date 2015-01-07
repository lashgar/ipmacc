
include ../../common/arch.mk

DUMPOUT= -DDUMPOUT

CC = g++
CC_FLAGS = $(DUMPOUT) 



ACC = ipmacc
ACC_FLAGS = $(ARCH) -O3 $(DUMPOUT)
ACL_FLAGS = -O3 $(DUMPOUT) 

cpu: 
	$(CC)  needle.cpp -o needle_$(CC)  $(CC_FLAGS) 
cuda:
	$(ACC) needle.cpp -o needle_$(ACC)_cuda $(ACC_FLAGS)
opencl:
	ta=nvopencl $(ACC) needle.cpp -o needle_$(ACC)_ocl $(ACL_FLAGS) 

clean:
	rm -f needle_$(ACC) needle_$(CC) a.out *_ipmacc* *txt
