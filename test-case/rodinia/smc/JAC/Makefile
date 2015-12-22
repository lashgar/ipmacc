
include ../../common/arch.mk

DUMPOUT= -DOUTPUT

# C compiler
CC = g++
CC_FLAGS = -O2 $(DUMPOUT)

ACC = ipmacc
ACC_FLAGS = -O2 $(DUMPOUT) $(ARCH) 
ACL_FLAGS = -O2 $(DUMPOUT)

cpu:
	$(CC)  jacobi_baseline.c -o JAC_$(CC)  $(CC_FLAGS) `ipmacc --cflags`

smc:
	$(ACC)  jacobi_smc.c -o JAC_$@  $(ACC_FLAGS)

cuda:
	$(ACC)  jacobi_baseline.c -o JAC_$@  $(ACC_FLAGS)

opencl:
	ta=nvopencl $(ACC) jacobi_baseline.c -o JAC_$@ $(ACL_FLAGS)

clean:
	rm -f JAC* a.out result*txt *_ipmacc.cu *_ipmacc.c
