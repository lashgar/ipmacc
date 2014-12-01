include ../../common/make.config

#C compiler
CC = g++

SRC = nearestNeighbor.cpp clutils.cpp utils.cpp

CC_FLAGS = -O3

EXE = nn

release:
	$(CC) $(CC_FLAGS) -lOpenCL  -fopenmp $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB)
	
clean: 
	rm -f $(EXE) 
