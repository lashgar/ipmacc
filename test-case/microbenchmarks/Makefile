CC = g++
CPP= cpp
ACC= ipmacc
ARRAYOBJS = arraybench_$(IDA).o  
ARCH= -arch=sm_35


ACC_FLAGS =  $(ARCH)
ACL_FLAGS = 
ACC_TARGET=nvcuda

all:
	$(MAKE) IDA=243 prog
	$(MAKE) IDA=729 prog
	$(MAKE) IDA=2187 prog
	$(MAKE) IDA=6561 prog
	$(MAKE) IDA=19683 prog
	$(MAKE) IDA=59049 prog
	$(MAKE) IDA=177147 prog
	$(MAKE) IDA=531441 prog
	$(MAKE) IDA=1594323 prog
	$(MAKE) IDA=4782969 prog

prog: arraybench_$(IDA)
# Multiple header files due to multiple array sizes, makes header file arraybench_*.h
arraybench_$(IDA).h: arraybench.h
	$(CPP) -DIDA=$(IDA) $(OMPFLAG) -P arraybench.h -o $@

# Multiple object files due to multiple array sizes, makes object file arraybench_*.o
arraybench_$(IDA).o: arraybench_$(IDA).h arraybench.c
	ta=$(ACC_TARGET) $(ACC) arraybench.c -c -o $@ -DIDA=$(IDA) 


# Multiple executables due to multiple array sizes, makes exe file arraybench_*
arraybench_$(IDA): $(ARRAYOBJS) arraybench.c
	$(CC) $(ARRAYOBJS) -lm -o $@ `ipmacc --ldflags`

clean: 
	rm *.o arraybench_*


