INCLUDES+= -I $(NVIDIA_COMPUTE_SDK_LOCATION)/C/common/inc/ -I $(CUDAHOME)/include/ -I $(NVIDIA_COMPUTE_SDK_LOCATION)/shared/inc/

all: $(OBJS) $(EXECUTABLE)
	@echo done

%.c_o: %.c
	gcc $< -c -o $@ $(CFLAGS)  $(INCLUDES)

%.cpp_o: %.cpp
	g++ $< -c -o $@ $(CFLAGS)  $(INCLUDES)

%.cu_o: %.cu
	nvcc $< -c -o $@ -I. -I $(NVIDIA_COMPUTE_SDK_LOCATION)/C/common/inc/ $(INCLUDES) $(CUFLAGS) -arch=sm_35

$(EXECUTABLE):
	g++ $(OBJS) -o $(EXECUTABLE) -L $(NVIDIA_COMPUTE_SDK_LOCATION)/C/lib/ -lcutil -L $(NVIDIA_COMPUTE_SDK_LOCATION)/shared/lib/ -lshrutil_x86_64 -L $(CUDAHOME)/lib64/ -lcudart $(LINKFLAGS)

clean:
	rm $(OBJS) $(EXECUTABLE) -f

clean_run:
	rm _cuobjdump_* gpgpusim_power_report__* -f

