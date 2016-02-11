all: directories perfbench

directories: objs/

objs/:
	/bin/mkdir -p objs/

objs/perfbench_ispc.o: perfbench.ispc
	ispc -O2 --arch=x86-64 --target=sse2-i32x4,sse4-i32x4,avx1-i32x8,avx2-i32x8 perfbench.ispc -o objs/perfbench_ispc.o -h objs/perfbench_ispc.h

objs/perfbench.o: perfbench.cpp
	clang++ perfbench.cpp -Iobjs/ -O2 -m64 -c -o objs/perfbench.o

objs/perfbench_serial.o: perfbench_serial.cpp
	ta=intelispc ipmacc perfbench_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/perfbench_serial.o
	#clang++ perfbench_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/perfbench_serial.o

objs/tasksys.o: ../tasksys.cpp
	clang++ ../tasksys.cpp -Iobjs/ -O2 -m64 -c -o objs/tasksys.o

perfbench: objs/perfbench_ispc.o objs/perfbench.o objs/perfbench_serial.o objs/perfbench_ispc_sse2.o objs/perfbench_ispc_sse4.o objs/perfbench_ispc_avx.o objs/perfbench_ispc_avx2.o
	clang++ -Iobjs/ -O2 -m64 -o perfbench objs/perfbench.o objs/perfbench_serial.o objs/perfbench_ispc.o objs/perfbench_ispc_sse2.o objs/perfbench_ispc_sse4.o objs/perfbench_ispc_avx.o objs/perfbench_ispc_avx2.o -lm -lpthread -lstdc++ `ipmacc --cflags` `ipmacc --ldflags`

clean:
	rm perfbench objs/ *ipmacc* -rf
