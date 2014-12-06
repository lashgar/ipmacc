CC=gcc
AR=ar

CFLAG=
LDFLAG=


ifeq ($(OPENCLSUPPORT),1)
 CFLAG += -I$(OPENCLINC)/ -D__NVOPENCL__ -DRALP
 LDFLAG+= -L$(OPENCLLIB)/ -lOpenCL
endif

ifeq ($(CUDASUPPORT),1)
 CFLAG += -I$(CUDAHOME)/include/ -D__NVCUDA__
 LDFLAG+= -L$(CUDAHOME)/lib64/ -lcudart
endif

all:
	@echo 'CFLAG : '$(CFLAG)
	@echo 'LDFLAG: '$(LDFLAG)
	#$(CC) -I$(CUDAHOME)/include/ -L$(CUDAHOME)/lib64/ -lcudart -I$(OPENCLINC)/ -L$(OPENCLLIB)/ -lOpenCL -D__NVCUDA__ -D__NVOPENCL__ openacc.c -c -fPIC
	$(CC) $(CFLAG) openacc.c -c -fPIC -g 
	mkdir ../lib -p
	gcc -shared -Wl,-soname,libopenacc.so -o libopenacc.so  openacc.o
	cp libopenacc.so ../lib

clean:
	rm *.a *.o *.so *.pyc -f

