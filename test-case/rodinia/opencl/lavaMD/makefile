include ../../common/make.config

# Example
# target: dependencies
	# command 1
	# command 2
          # .
          # .
          # .
	# command n

C_C = gcc
OMP_LIB = -lgomp
OMP_FLAG = -fopenmp
OCL_LIB =	-L$(OPENCLLIB) \
			-lOpenCL
OCL_INC = -I$(OPENCLINC)

# link objects together
a.out:		main.o \
			./kernel/kernel_gpu_opencl_wrapper.o \
			./util/num/num.o \
			./util/timer/timer.o \
			./util/opencl/opencl.o
	$(C_C)	main.o \
			./kernel/kernel_gpu_opencl_wrapper.o \
			./util/num/num.o \
			./util/timer/timer.o \
			./util/opencl/opencl.o \
			-lm \
			$(OCL_LIB) \
			-o lavaMD

# compile function files into objects
main.o:		main.h \
			main.c \
			./kernel/kernel_gpu_opencl_wrapper.h \
			./kernel/kernel_gpu_opencl_wrapper.c \
			./util/num/num.h \
			./util/num/num.c \
			./util/timer/timer.h \
			./util/timer/timer.c \
			./util/opencl/opencl.h \
			./util/opencl/opencl.c
	$(C_C)	main.c \
			-c \
			-o main.o \
			-O3

./kernel/kernel_gpu_opencl_wrapper.o:	./kernel/kernel_gpu_opencl_wrapper.h \
										./kernel/kernel_gpu_opencl_wrapper.c
	$(C_C)								./kernel/kernel_gpu_opencl_wrapper.c \
										$(OCL_INC) \
										-c \
										-o ./kernel/kernel_gpu_opencl_wrapper.o \
										-O3

./util/num/num.o:	./util/num/num.h \
					./util/num/num.c
	$(C_C)			./util/num/num.c \
					-c \
					-o ./util/num/num.o \
					-O3

./util/timer/timer.o:	./util/timer/timer.h \
						./util/timer/timer.c
	$(C_C)				./util/timer/timer.c \
						-c \
						-o ./util/timer/timer.o \
						-O3

./util/opencl/opencl.o:	./util/opencl/opencl.h \
						./util/opencl/opencl.c
	$(C_C)				./util/opencl/opencl.c \
						$(OCL_INC) \
						-c \
						-o ./util/opencl/opencl.o \
						-O3

# delete all object and executable files
clean:
	rm	*.o lavaMD \
		./kernel/*.o \
		./util/num/*.o \
		./util/timer/*.o \
		./util/opencl/*.o \
                ./util/cuda/*.o
