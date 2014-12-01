include ../../common/make.config

# OpenCL installation path      
# OPENCL_DIR = /home/mwb7w/NVIDIA_GPU_Computing_SDK/
# OPENCL_DIR = /home/mwb7w/ati-stream-sdk-v2.2-lnx64/

#DUMPOUT= -DDUMPOUT

CC = gcc $(DUMPOUT) 
CC_FLAGS = -g -O2 -Wall

EXE = hotspot

$(EXE): hotspot.c hotspot.h OpenCL_helper_library.c OpenCL_helper_library.h
	$(CC) $(CC_FLAGS) -o $(EXE) -I$(OPENCLINC) OpenCL_helper_library.c hotspot.c -L$(OPENCLLIB) -lOpenCL

clean:
	rm -f $(EXE)
