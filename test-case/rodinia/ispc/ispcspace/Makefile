
#SIZEFLAGS=-DSIZEX=32768 -DSIZEY=1 -DSIZEZ=1

all: ispc_add_1d opencl_add_1d opencl_add_2d ispc_add_2d_task ispc_add_2d_foreach_tile opencl_add_3d ispc_add_3d_foreach_tile ispc_add_3d_task_foreach_tile ispc_add_3d_task_serial

ispc_add_1d: ispc_add_1d.ispc ispc_add_1d.c
	ispc ispc_add_1d.ispc -o ispc_add_1d_kernel.o
	g++ `ta=intelispc ipmacc --cflags` ispc_add_1d.c -c -o ispc_add_1d.o
	g++ `ta=intelispc ipmacc --ldflags` ispc_add_1d.o ispc_add_1d_kernel.o -o ispc_add_1d

ispc_add_2d_task: ispc_add_2d.c ispc_add_2d_task.ispc
	ispc ispc_add_2d_task.ispc -o ispc_add_2d_task_kernel.o
	g++ `ta=intelispc ipmacc --cflags` ispc_add_2d.c -c -o ispc_add_2d.o
	g++ `ta=intelispc ipmacc --ldflags` ispc_add_2d.o ispc_add_2d_task_kernel.o -o ispc_add_2d_task

ispc_add_2d_foreach_tile: ispc_add_2d.c ispc_add_2d_foreach_tile.ispc
	ispc ispc_add_2d_foreach_tile.ispc -o ispc_add_2d_foreach_tile_kernel.o
	g++ `ta=intelispc ipmacc --cflags` ispc_add_2d.c -c -o ispc_add_2d.o
	g++ `ta=intelispc ipmacc --ldflags` ispc_add_2d.o ispc_add_2d_foreach_tile_kernel.o -o ispc_add_2d_foreach_tile

ispc_add_3d_foreach_tile: ispc_add_3d.c ispc_add_3d_foreach_tile.ispc 
	ispc ispc_add_3d_foreach_tile.ispc -o ispc_add_3d_foreach_tile_kernel.o
	g++ `ta=intelispc ipmacc --cflags` ispc_add_3d.c -c -o ispc_add_3d.o
	g++ `ta=intelispc ipmacc --ldflags` ispc_add_3d.o ispc_add_3d_foreach_tile_kernel.o -o ispc_add_3d_foreach_tile

ispc_add_3d_task_foreach_tile: ispc_add_3d.c ispc_add_3d_task_foreach_tile.ispc
	ispc ispc_add_3d_task_foreach_tile.ispc -o ispc_add_3d_task_foreach_tile_kernel.o
	g++ `ta=intelispc ipmacc --cflags` ispc_add_3d.c -c -o ispc_add_2d.o
	g++ `ta=intelispc ipmacc --ldflags` ispc_add_3d.o ispc_add_3d_task_foreach_tile_kernel.o -o ispc_add_3d_task_foreach_tile

ispc_add_3d_task_serial: ispc_add_3d.c ispc_add_3d_task_serial.ispc
	ispc ispc_add_3d_task_serial.ispc -o ispc_add_3d_task_serial_kernel.o
	g++ `ta=intelispc ipmacc --cflags` ispc_add_3d.c -c -o ispc_add_3d.o
	g++ `ta=intelispc ipmacc --ldflags` ispc_add_3d.o ispc_add_3d_task_serial_kernel.o -o ispc_add_3d_task_serial

opencl_add_1d: acc_add_1d.c
	ta=nvopencl ipmacc acc_add_1d.c -o opencl_add_1d

opencl_add_2d: acc_add_2d.c
	ta=nvopencl ipmacc acc_add_2d.c -o opencl_add_2d

opencl_add_3d: acc_add_3d.c
	ta=nvopencl ipmacc acc_add_3d.c -o opencl_add_3d

clean:
	rm *ipmacc* *.o -f

clean_all:
	rm -f opencl_add_1d ispc_add_1d opencl_add_2d ispc_add_2d_task ispc_add_2d_foreach_tile opencl_add_3d ispc_add_1d ispc_add_2d_foreach_tile ispc_add_2d_task ispc_add_3d_foreach_tile ispc_add_3d_task_foreach_tile ispc_add_3d_task_serial opencl_add_1d opencl_add_2d opencl_add_3d

