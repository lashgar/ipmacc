
include ../../../common/arch.mk

# C compiler
CXX = g++
CXX_FLAGS = -O2

ACC = ipmacc
ACC_FLAGS = -O2 $(ARCH)
ACL_FLAGS = -O2

cpu: 
	$(CXX) srad.cpp -o srad_$(CXX) $(CXX_FLAGS)

cuda:
	$(ACC) srad.cpp -o srad_cuda $(ACC_FLAGS)

opencl:
	ta=nvopencl $(ACC) srad.cpp -o srad_opencl $(ACL_FLAGS)

clean:
	rm -f srad_$(CXX) srad_cuda srad_opencl *_ipmacc.c* output*txt
