all: directories noise_ocl

directories: objs/

objs/:
	/bin/mkdir -p objs/

objs/noise_ispc.o: noise.ispc
	ispc -O2 --arch=x86-64 --target=sse2-i32x4,sse4-i32x4,avx1-i32x16,avx2-i32x16 noise.ispc -o objs/noise_ispc.o -h objs/noise_ispc.h

objs/noise.o: noise.cpp
	clang++ noise.cpp -Iobjs/ -O2 -m64 -c -o objs/noise.o `ta=nvcuda ipmacc --cflags`

objs/noise_serial.o: noise_serial.cpp
	ta=nvcuda ipmacc noise_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/noise_serial.o

objs/tasksys.o: ../tasksys.cpp
	clang++ ../tasksys.cpp -Iobjs/ -O2 -m64 -c -o objs/tasksys.o

noise_ocl: objs/noise_ispc.o  objs/noise.o objs/noise_serial.o objs/noise_ispc_sse2.o objs/noise_ispc_sse4.o objs/noise_ispc_avx.o objs/noise_ispc_avx2.o
	clang++ -Iobjs/ -O2 -m64 -o noise_ocl objs/noise.o objs/noise_serial.o objs/noise_ispc.o objs/noise_ispc_sse2.o objs/noise_ispc_sse4.o objs/noise_ispc_avx.o objs/noise_ispc_avx2.o -lm -lpthread -lstdc++ `ipmacc --cflags` `ipmacc --ldflags`

clean:
	rm noise objs/ *ipmacc* -rf
