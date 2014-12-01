include ../../common/arch.mk

# C compiler
#CC = pathcc
#CC_FLAGS = -acc -O2

CC = g++
ACC = ipmacc
CC_FLAGS = -O3 
ACC_FLAGS = $(ARCH) -O3
ACL_FLAGS= -O3
#CC_FLAGS = -O3 -I /usr/include/i386-linux-gnu/ -L /usr/lib/i386-linux-gnu/

cpu: imagenet.o facetrain.o
	$(CC) backprop.c -c -o backprop_g++.o $(CC_FLAGS)
	$(CC) backprop_kernel.c -c -o backprop_kernel_g++.o $(CC_FLAGS) 
	$(CC) backprop_g++.o facetrain.o imagenet.o backprop_kernel_g++.o -o backprop_g++ -lm $(CC_FLAGS) 

cuda: imagenet.o facetrain.o
	$(ACC) backprop.c -c -o backprop_$(ACC)_cuda.o $(ACC_FLAGS)
	$(ACC) backprop_kernel.c -c -o backprop_kernel_$(ACC)_cuda.o $(ACC_FLAGS) 
	$(CC) `ipmacc --ldflags` backprop_$(ACC)_cuda.o facetrain.o imagenet.o backprop_kernel_$(ACC)_cuda.o -o backprop_$(ACC)_cuda -lm $(CC_FLAGS) 

opencl: imagenet.o facetrain.o
	ta=nvopencl $(ACC) backprop_kernel.c -c -o backprop_kernel_$(ACC)_opencl.o 
	ta=nvopencl $(ACC) backprop.c -c -o backprop_$(ACC)_opencl.o $(ACL_FLAGS)
	$(CC) `ipmacc --ldflags` backprop_$(ACC)_opencl.o facetrain.o imagenet.o backprop_kernel_$(ACC)_opencl.o -o backprop_$(ACC)_opencl -lm $(ACL_FLAGS) 

#%.o: %.[ch]
#	$(CC) $(CC_FLAGS) $< -c

facetrain.o: 
	$(CC) facetrain.c -c $(CC_FLAGS) 
	
imagenet.o: 
	$(CC) $(CC_FLAGS) imagenet.c -c


clean:
	rm -f *.o *~ backprop_cuda.linkinfo backprop_g++ *ipmacc* 
