include ../../common/arch.mk

# C compiler
DUMPOUT = -DDUMPOUT
#DUMPOUT = 

CC = g++
CC_FLAGS = -O2 $(DUMPOUT)

ACC = ipmacc
ACC_FLAGS = $(ARCH) -O2 $(DUMPOUT)
ACL_FLAGS = -O2 $(DUMPOUT) -pg

cpu: 
	$(CC)  bfs_IPMACC.cpp -o bfs_g++    $(CC_FLAGS) 

cuda:
	$(ACC) bfs_IPMACC.cpp -o bfs_cuda $(ACC_FLAGS) 

opencl:
	ta=nvopencl $(ACC) bfs_IPMACC.cpp -o bfs_opencl $(ACL_FLAGS) 

clean:
	rm -f bfs_cuda bfs_g++ bfs_opencl result*txt  *_ipmacc.c* *.txt *.log
