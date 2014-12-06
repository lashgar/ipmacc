
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
	$(ACC) hotspot_openacc_IPM.cpp -o smc_ghostzone  $(ACC_FLAGS) -Xptxas=-v
	#nvcc hotspot_openacc_IPM_ipmacc.cu -o smc_ghostzone  $(ACC_FLAGS)  `ipmacc --cflags` `ipmacc --ldflags`

clean:
	rm -f hotspot_$(CC) hotspot_$(ACC)* *.o a.out result*txt *_ipmacc.cu *_ipmacc.cpp .testlog* .perflog*
