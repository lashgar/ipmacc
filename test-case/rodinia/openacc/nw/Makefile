
include ../../common/arch.mk

CC = g++
CC_FLAGS = 

ACC = ipmacc
ACC_FLAGS = $(ARCH) -O3 
ACL_FLAGS = -O3 

cpu: 
	$(CC)  needle.cpp -o needle_$(CC)  $(CC_FLAGS) 
cuda:
	$(ACC) needle.cpp -o needle_$(ACC)_cuda $(ACC_FLAGS)
opencl:
	ta=nvopencl $(ACC) needle.cpp -o needle_$(ACC)_opencl $(ACL_FLAGS) 

clean:
	rm -f needle_$(ACC) needle_$(CC) a.out *_ipmacc* result*txt
