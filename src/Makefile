CC=gcc
CXX=g++
AR=ar

CFLAG=
LDFLAG=


ifeq ($(OPENCLSUPPORT),1)
 CFLAG += -I$(OPENCLINC)/ -D__NVOPENCL__ # -DRALP
 LDFLAG+= -L$(OPENCLLIB)/ -lOpenCL
endif

ifeq ($(CUDASUPPORT),1)
 CFLAG += -I$(CUDAHOME)/include/ -D__NVCUDA__
 LDFLAG+= -L$(CUDAHOME)/lib64/ -lcudart
endif



all: libopenacc listdevices
	./listdevices CUDA
	./listdevices OCL

libopenacc: openacc.o openacc_container.o tasksys.o
	@echo 'CFLAG : '$(CFLAG)
	@echo 'LDFLAG: '$(LDFLAG)
	@#$(CC) -I$(CUDAHOME)/include/ -L$(CUDAHOME)/lib64/ -lcudart -I$(OPENCLINC)/ -L$(OPENCLLIB)/ -lOpenCL -D__NVCUDA__ -D__NVOPENCL__ openacc.c -c -fPIC
	mkdir ../lib -p
	g++ -shared -Wl,-soname,libopenacc.so -o libopenacc.so  openacc.o openacc_container.o
	cp libopenacc.so ../lib

openacc.o: openacc.c
	$(CC) $(CFLAG) openacc.c -c -fPIC -g 

openacc_container.o: openacc_container.cpp 
	$(CXX) $(CFLAG) openacc_container.cpp -c -fPIC -g -std=c++0x -DOBJ

tasksys.o:
ifeq ($(ISPCSUPPORT),1)
	$(CXX) $(ISPCHOME)/examples/tasksys.cpp -O2 -c -o $(IPMACCROOT)/src/tasksys.o
endif

listdevices: listdevices.c
	$(CC) listdevices.c -o listdevices -fPIC -g `ipmacc --cflags` `ipmacc --ldflags`

clean:
	rm *.a *.o *.so *.pyc listdevices -f

