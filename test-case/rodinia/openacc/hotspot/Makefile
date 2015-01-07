
include ../../common/arch.mk

DUMPOUT= -DOUTPUT

# C compiler
CC = g++
CC_FLAGS = -O2 $(DUMPOUT)

ACC = ipmacc
ACC_FLAGS = -O2 $(DUMPOUT) $(ARCH)
ACL_FLAGS = -O2 $(DUMPOUT)

cpu:
	$(CC)  hotspot_openacc_IPM.cpp -o hotspot_$(CC)  $(CC_FLAGS) 

cuda:
	$(ACC) hotspot_openacc_IPM.cpp -o hotspot_$(ACC)_cuda $(ACC_FLAGS) 
	#nvcc `ipmacc --cflags` `ipmacc --ldflags` hotspot_openacc_IPM_ipmacc.cu -o hotspot_$(ACC)_cuda $(ACC_FLAGS) 

opencl:
	ta=nvopencl $(ACC) hotspot_openacc_IPM.cpp -o hotspot_$(ACC)_opencl $(ACL_FLAGS) 

clean:
	rm -f hotspot_$(CC) hotspot_$(ACC)* *.o a.out result*txt *_ipmacc.cu *_ipmacc.cpp *txt .perf*
