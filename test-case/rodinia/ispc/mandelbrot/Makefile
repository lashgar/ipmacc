
all: directories objs/mandelbrot_ispc.o objs/mandelbrot.o objs/mandelbrot_serial.o objs/tasksys.o mandelbrot

directories: objs/

objs/:
	/bin/mkdir -p objs/

objs/mandelbrot_ispc.o: mandelbrot.ispc
	#ispc -O2 --arch=x86-64 mandelbrot.ispc -o objs/mandelbrot_ispc.o -h objs/mandelbrot_ispc.h
	ispc -O2 --arch=x86-64 --target=sse2-i32x4,sse4-i32x8,avx1-i32x16,avx2-i32x16 mandelbrot.ispc -o objs/mandelbrot_ispc.o -h objs/mandelbrot_ispc.h

objs/mandelbrot.o: mandelbrot.cpp
	clang++ mandelbrot.cpp -Iobjs/ -O2 -m64 -c -o objs/mandelbrot.o

objs/mandelbrot_serial.o: mandelbrot_serial.cpp
	#clang++ mandelbrot_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/mandelbrot_serial.o
	ta=intelispc ipmacc mandelbrot_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/mandelbrot_serial.o

objs/tasksys.o:
	clang++ ../tasksys.cpp -Iobjs/ -O2 -m64 -c -o objs/tasksys.o

mandelbrot: objs/mandelbrot.o objs/mandelbrot_serial.o objs/mandelbrot_ispc.o
	clang++ -Iobjs/ -O2 -m64 -o mandelbrot objs/mandelbrot.o objs/mandelbrot_serial.o objs/mandelbrot_ispc.o objs/mandelbrot_ispc_sse2.o objs/mandelbrot_ispc_sse4.o objs/mandelbrot_ispc_avx.o objs/mandelbrot_ispc_avx2.o -lm -lpthread -lstdc++ `ipmacc --ldflags`
	#clang++ -Iobjs/ -O2 -m64 -o mandelbrot objs/mandelbrot.o objs/mandelbrot_serial.o objs/mandelbrot_ispc.o -lm -lpthread -lstdc++ `ipmacc --ldflags`

clean:
	rm objs/ mandelbrot -rf *ipmacc*
