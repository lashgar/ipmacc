
all: v1_cpu v1_cuda v1_opencl v2_cpu v2_cuda v2_opencl

v1_cpu:
	cd srad_v1; 	make cpu
v1_cuda:
	cd srad_v1; 	make cuda
v1_opencl:
	cd srad_v1; 	make opencl

v2_cpu:
	cd srad_v2; 	make cpu
v2_cuda:
	cd srad_v2; 	make cuda
v2_opencl:
	cd srad_v2; 	make opencl

cuda:
	cd srad_v1; 	make cuda
	cd srad_v2; 	make cuda

opencl:
	make opencl -C srad_v1

clean: v1_clean v2_clean

v1_clean:
	cd srad_v1; 	make clean
	
v2_clean:
	cd srad_v2; 	make clean

