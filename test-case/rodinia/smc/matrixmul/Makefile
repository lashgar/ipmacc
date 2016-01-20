
include ../../common/arch.mk

DUMPOUT= -DOUTPUT

# C compiler
CC = g++
CC_FLAGS = -O2 $(DUMPOUT)

ACC = ipmacc
ACC_FLAGS = -O2 $(DUMPOUT) $(ARCH) 
ACL_FLAGS = -O2 $(DUMPOUT)

cpu:
	$(CC)  matrixMul.cpp -o matMul_$(CC)  $(CC_FLAGS)

smc:
	$(ACC) matrixMul.cpp -o matMul_smc  $(ACC_FLAGS) -Xptxas=-v

nosmc:
	$(ACC) matrixMul_nosmc.cpp -o matMul_nosmc  $(ACC_FLAGS) -Xptxas=-v

cuda:
	nvcc matrixMul_cuda.cu -o matMul_cuda `ipmacc --cflags` `ipmacc --ldflags` -Xptxas=-v

baseline:
	$(ACC) matrixMul_baseline.cpp -o matMul_baseline  $(ACC_FLAGS) -Xptxas=-v

opencl:
	ta=nvopencl $(ACC) matrixMul.cpp -o matMul_$(ACC)_opencl $(ACL_FLAGS)

clean:
	rm -f matMul** *.o a.out result*txt *_ipmacc.cu *_ipmacc.cpp


