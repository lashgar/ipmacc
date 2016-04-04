
all: directories objs/mandelbrot_tasks_ispc.o objs/mandelbrot_tasks.o objs/mandelbrot_tasks_serial.o mandelbrot_tasks

directories: objs/

objs/:
	/bin/mkdir -p objs/

objs/mandelbrot_tasks_ispc.o: mandelbrot_tasks.ispc
	ispc -O2 --arch=x86-64 --target=sse2-i32x4,sse4-i32x8,avx1-i32x16,avx2-i32x16 mandelbrot_tasks.ispc -o objs/mandelbrot_tasks_ispc.o -h objs/mandelbrot_tasks_ispc.h

objs/mandelbrot_tasks.o: mandelbrot_tasks.cpp
	clang++ mandelbrot_tasks.cpp -Iobjs/ -O2 -m64 -c -o objs/mandelbrot_tasks.o

objs/mandelbrot_tasks_serial.o: mandelbrot_tasks_serial.cpp
	ta=intelispc ipmacc mandelbrot_tasks_serial.cpp -Iobjs/ -O2 -m64 -c -o objs/mandelbrot_tasks_serial.o

mandelbrot_tasks:  objs/mandelbrot_tasks.o objs/mandelbrot_tasks_serial.o objs/mandelbrot_tasks_ispc.o
	clang++ -Iobjs/ -O2 -m64 -o mandelbrot_tasks objs/mandelbrot_tasks.o objs/mandelbrot_tasks_serial.o objs/mandelbrot_tasks_ispc.o objs/mandelbrot_tasks_ispc_sse2.o objs/mandelbrot_tasks_ispc_sse4.o objs/mandelbrot_tasks_ispc_avx.o objs/mandelbrot_tasks_ispc_avx2.o -lm -lpthread -lstdc++ `ipmacc --ldflags`

clean:
	rm objs/ mandelbrot_tasks -rf *ipmacc*
