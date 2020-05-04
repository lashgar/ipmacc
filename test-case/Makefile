
CC=ipmacc
CFLAGS=
IPMACCFLAGS=
LDFLGAS=

testcuda:
	# disabled tests (not implemented): matMulDynamic_gang.c vectorAdd_gang.c
	@for bench in  apitest.c matMulDynamic.c multiple_kernels.c private.c vectorAdd.c implicit_array.c pgi_acc_c3.c scalarVar.c deviceptr.c matMul.c present_clause.c undefined_var.c function_call.c ; do \
		echo -n "testing $$bench " ; \
		echo -n "compiling ... " ; \
		$(IPMACCFLAGS) $(CC) $(CFLAGS) $(LDFLAGS) $$bench -o $$bench.cuda > /dev/null; \
		echo -n "running ... " ; \
		./$$bench.cuda > /dev/null ; \
	done;
#	$(IPMACCFLAGS) $(CC) $(CFLAGS) $(LDFLAGS) 
#testcl:
testopencl:
	# disabled tests (not implemented): matMulDynamic_gang.c vectorAdd_gang.c
	for bench in  apitest.c matMulDynamic.c multiple_kernels.c private.c vectorAdd.c implicit_array.c pgi_acc_c3.c scalarVar.c matMul.c present_clause.c undefined_var.c function_call.c ; do \
		echo '====================================================' ; \
		echo -n "testing $$bench " ; \
		echo -n "compiling ... " ; \
		ta=nvopencl $(IPMACCFLAGS) $(CC) $(CFLAGS) $(LDFLAGS) $$bench -o $$bench.ocl > /dev/null; \
		echo -n '  running ... ' ; \
		./$$bench.ocl > /dev/null ; \
	done;

precisioncuda:
	echo 'compiling ...' ; 
	$(IPMACCFLAGS) $(CC) $(CFLAGS) $(LDFLAGS) precision.c -o prec.cuda --ta nvcuda  -arch=sm_13 > /dev/null; 
	echo '  running ...' ; 
	./prec.cuda

precisionopencl:
	echo 'compiling ...' ; 
	$(IPMACCFLAGS) $(CC) $(CFLAGS) $(LDFLAGS) precision.c -o prec.cuda --ta nvopencl > /dev/null; 
	echo '  running ...' ; 
	./prec.ocl

smccuda:
	$(CC) smc_readonly_micbench.c -I /share/users/alashgar/NVIDIA_GPU_Computing_SDK/C/common/inc/ -L/share/users/alashgar/NVIDIA_GPU_Computing_SDK/C/lib -lcutil -o smc_readonly.cuda

clean:
	rm *.o *.cuda *.ocl a.out *_ipmacc.c *_ipmacc.cu *_ipmacc.cpp *_ipmacc.ispc -f
	make clean -C rodinia/
	make clean -C microbenchmarks/
