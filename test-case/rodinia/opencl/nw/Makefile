include ../../common/make.config

#C compiler
CC = g++

CC_FLAGS = -Wall -O3

EXE = nw

$(EXE): nw.c
	$(CC) $(CC_FLAGS) -o $(EXE) nw.c -I$(OPENCLINC) -L$(OPENCLLIB) -lOpenCL

clean:
	rm -f $(EXE)
