
all: directories objs/stencil_ispc.o objs/stencil.o objs/stencil_serial.o objs/tasksys.o objs/stencil_ispc_sse2.o objs/stencil_ispc_sse4.o objs/stencil_ispc_avx.o objs/stencil_ispc_avx2.o stencil

directories: objs/

objs/:
	/bin/mkdir -p objs/

objs/stencil_ispc.o: stencil.ispc
	ispc -O2 --arch=x86-64 --target=sse2-i32x4,sse4-i32x8,avx1-i32x16,avx2-i32x16 stencil.ispc -o objs/stencil_ispc.o -h objs/stencil_ispc.h

objs/stencil.o: stencil.cpp
	clang++ stencil.cpp -Iobjs/ -O2 -m64 -c -o objs/stencil.o

objs/stencil_serial.o: stencil_serial.cpp
	ta=intelispc ipmacc stencil_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/stencil_serial.o

objs/tasksys.o: ../tasksys.cpp
	clang++ ../tasksys.cpp -Iobjs/ -O2 -m64 -c -o objs/tasksys.o

stencil: objs/stencil.o objs/stencil_serial.o objs/tasksys.o objs/stencil_ispc.o objs/stencil_ispc_sse2.o objs/stencil_ispc_sse4.o objs/stencil_ispc_avx.o objs/stencil_ispc_avx2.o
	clang++ -Iobjs/ -O2 -m64 -o stencil objs/stencil.o objs/stencil_serial.o objs/stencil_ispc.o objs/stencil_ispc_sse2.o objs/stencil_ispc_sse4.o objs/stencil_ispc_avx.o objs/stencil_ispc_avx2.o -lm -lpthread -lstdc++ `ipmacc --cflags` `ipmacc --ldflags`

clean:
	rm objs/ stencil *_ipmacc* -rf
