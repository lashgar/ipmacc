include ../../../common/make.config

INC = -I$(OPENCLINC) -I../common
LIB = -L$(OPENCLLIB)

#C compiler
CC = g++
CC_FLAGS = -g -O3 -Wall

EXE = lud

$(EXE): lud.cpp
	$(CC) $(CC_FLAGS) -o $(EXE) lud.cpp ../common/common.c $(INC) $(LIB) -lOpenCL

clean:
	rm -f $(EXE)
