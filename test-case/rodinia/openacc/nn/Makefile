
include ../../common/arch.mk

CC = g++ 
CC_FLAGS =  -O3 


ACC= ipmacc
ACC_FLAGS =  -O3 $(ARCH) 
ACL_FLAGS =  -O3 


cpu: hurricane_gen
	$(CC)  nn_openacc.cpp $(CC_FLAGS)  -o nn_$(CC)  -lm

cuda: hurricane_gen
	$(ACC) nn_openacc.cpp $(ACC_FLAGS) -o nn_$(ACC)_cuda -lm

opencl: hurricane_gen
	ta=nvopencl $(ACC) nn_openacc.cpp $(ACL_FLAGS) -o nn_$(ACC)_ocl -lm

ispc: hurricane_gen
	ta=intelispc $(ACC) nn_openacc.cpp $(ACL_FLAGS) -o nn_$(ACC)_ispc -lm

hurricane_gen:
	$(CC) hurricane_gen.c $(CC_FLAGS) -lm -o hurricane_gen
	 
clean :
	rm -f *.o nn_$(ACC) nn_$(CC) hurricane_gen *_ipmacc* *txt *ispc out.*
