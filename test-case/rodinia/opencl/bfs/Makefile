include ../../common/make.config

#C compiler
CC = g++

SRC = bfs.cpp timer.cc

CC_FLAGS = -g -O2

EXE = bfs

release:$(SRC)
	$(CC) $(CC_FLAGS) -lOpenCL  -fopenmp $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB)

errmsg:$(SRC)
	$(CC) $(CC_FLAGS) -lOpenCL -fopenmp $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB) -D ERRMSG PTX_MSG
	
ptx:$(SRC)
	$(CC) $(CC_FLAGS) -lOpenCL -fopenmp $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB) -D PTX_MSG

profile:$(SRC)
	$(CC) $(CC_FLAGS) -lOpenCL -fopenmp $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB) -D PROFILING
	
res:$(SRC)
	$(CC) $(CC_FLAGS) -lOpenCL -fopenmp $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB) -D RES_MSG
	
debug: $(SRC)
	$(CC) $(CC_FLAGS) -lOpenCL $(SRC) -o $(EXE) -I$(OPENCLINC) -L$(OPENCLLIB)
	
run:
	./$(EXE)
	
clean: $(SRC)
	rm -f $(EXE) $(EXE).linkinfo result*
