

all:
	make -C shared/src/
	make -C OpenCL/common
	make -C OpenCL/src/oclNbody/

clean:
	make clean -C OpenCL/src/oclNbody
	make clean -C OpenCL/common
	make clean -C shared/src/
	rm oclNbody_Regression.dat  oclNbody.txt SdkMasterLog.csv shared/src/*.o -f
