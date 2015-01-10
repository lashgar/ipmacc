include ../../common/make.config
include ../../common/arch.mk

#ARCH= -arch=sm_20
CC := $(CUDA_DIR)/bin/nvcc -O2 $(ARCH) -DDUMPOUT

INCLUDE := $(CUDA_DIR)/include

SRC = hotspot.cu 

EXE = hotspot

release: $(SRC)
	$(CC) $(SRC) -o $(EXE) -I$(INCLUDE) -L$(CUDA_LIB_DIR) 

enum: $(SRC)
	$(CC) -deviceemu $(SRC) -o $(EXE) -I$(INCLUDE) -L$(CUDA_LIB_DIR) 

debug: $(SRC)
	$(CC) $(SRC) -o $(EXE) -I$(INCLUDE) -L$(CUDA_LIB_DIR) 

debugenum: $(SRC)
	$(CC) -deviceemu $(SRC) -o $(EXE) -I$(INCLUDE) -L$(CUDA_LIB_DIR) 

clean: $(SRC)
	rm -f $(EXE) $(EXE).linkinfo result.txt .perf* .testlog* output.out
