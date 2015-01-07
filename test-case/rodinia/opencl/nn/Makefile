include ../../common/make.config

#C compiler
CC = g++

SRC = nearestNeighbor.cpp clutils.cpp utils.cpp

CC_FLAGS = -O3 -g -m64

EXE = nn

release:
	#$(CC) $(CC_FLAGS) -lOpenCL  $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB)
	$(CC) $(CC_FLAGS) -lOpenCL  $(SRC) -o $(EXE) `ipmacc --cflags` `ipmacc --ldflags`
	
clean: 
	rm -f $(EXE) *log *o
