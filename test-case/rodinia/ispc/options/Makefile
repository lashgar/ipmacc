all: directories options

directories: objs/

objs/:
	/bin/mkdir -p objs/

objs/options_ispc.o: options.ispc
	ispc -O2 --arch=x86-64 --target=sse2-i32x4,sse4-i32x8,avx1-i32x16,avx2-i32x16 options.ispc -o objs/options_ispc.o -h objs/options_ispc.h

objs/options.o: options.cpp
	clang++ options.cpp -Iobjs/ -O2 -m64 -c -o objs/options.o

objs/options_serial.o: options_serial.cpp
	#clang++ options_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/options_serial.o
	ta=intelispc ipmacc options_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/options_serial.o

objs/tasksys.o: ../tasksys.cpp
	clang++ ../tasksys.cpp -Iobjs/ -O2 -m64 -c -o objs/tasksys.o

options: objs/options_ispc.o objs/options.o objs/options_serial.o objs/options_ispc_sse2.o objs/options_ispc_sse4.o objs/options_ispc_avx.o objs/options_ispc_avx2.o 
	clang++ -Iobjs/ -O2 -m64 -o options objs/options.o objs/options_serial.o objs/options_ispc.o objs/options_ispc_sse2.o objs/options_ispc_sse4.o objs/options_ispc_avx.o objs/options_ispc_avx2.o -lm -lpthread -lstdc++ `ipmacc --ldflags`

clean:
	rm options objs/ *ipmacc* -rf
