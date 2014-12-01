#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#include <CL/cl.h>
extern cl_int __ipmacc_clerr ;
extern cl_context __ipmacc_clctx ;
extern size_t __ipmacc_parmsz;
extern cl_device_id* __ipmacc_cldevs;
extern cl_command_queue __ipmacc_command_queue;


#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include <iostream>
#include "openacc.h"

using namespace std;


int main()
{
  int arr [100000];
  int sum = 0;
  int sum2 = 0;
  int arr_size = 1;

    #ifdef __NVCUDA__
  acc_init(acc_device_nvcuda);
    #endif
    #ifdef __NVOPENCL__
  acc_init(acc_device_nvocl);
  
    #endif



  srand(time(NULL));

  while (arr_size < 100000) {
    sum = 0;
    sum2 = 0;
    for (int i = 0; i < arr_size; ++i) {
      arr [i] = rand() % 100;
    }
    
    
    

	ipmacc_prompt((char*)"IPMACC: memory allocation arr\n");
acc_create((void*)arr,100000*sizeof(int));
	ipmacc_prompt((char*)"IPMACC: memory copyin arr\n");
acc_copyin((void*)arr,100000*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation sum\n");
int* __ipmacc_reduction_array_sum=NULL;
if(__ipmacc_reduction_array_sum==NULL){
__ipmacc_reduction_array_sum=(int*)malloc((((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));
acc_create((void*)__ipmacc_reduction_array_sum,(((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));
for(int __ipmacc_initialize_rv=0; __ipmacc_initialize_rv<(((abs((int)((arr_size))-0))/(1))/256+1); __ipmacc_initialize_rv++){
__ipmacc_reduction_array_sum[__ipmacc_initialize_rv]= 0;
}
acc_pcopyin((void*)__ipmacc_reduction_array_sum,(((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));
}

/* kernel call statement*/
const char* kernelSource0 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_0(__global int* arr,int arr_size,__global int* sum__ipmacc_reductionarray_internal){\nint __kernel_getuid=get_global_id(0);\n__local int __kernel_reduction_shmem_int[256];\nint __kernel_reduction_iterator=0;\nint sum;{\n{\n{\nint i=0+(__kernel_getuid);\nif( i < arr_size)\n{\n\n{\nint sum=0;\n\n{\n      sum += arr [i];\n    }\n\n\n\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n__kernel_reduction_shmem_int[get_local_id(0)]=sum;\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\nfor(__kernel_reduction_iterator=256/2;__kernel_reduction_iterator>0; __kernel_reduction_iterator>>=1) {\nif(get_local_id(0)<__kernel_reduction_iterator){\n__kernel_reduction_shmem_int[get_local_id(0)]=__kernel_reduction_shmem_int[get_local_id(0)]+__kernel_reduction_shmem_int[get_local_id(0)+__kernel_reduction_iterator];\n}\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n}\n}\nif(get_local_id(0)==0){\nsum__ipmacc_reductionarray_internal[get_group_id(0)]=__kernel_reduction_shmem_int[0];\n}\n\n}\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm0;
__ipmacc_clpgm0=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource0, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags0[128];
sprintf(__ipmacc_clcompileflags0, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm0, 0, NULL, __ipmacc_clcompileflags0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm0, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm0, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
cl_kernel __ipmacc_clkern0 = clCreateKernel(__ipmacc_clpgm0, "__generated_kernel_region_0", &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arr);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
int immediate=arr_size;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 1, sizeof(int), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(__ipmacc_reduction_array_sum);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 2, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",((((abs((int)((arr_size))-0))/(1))/256)+1)*256,256);
size_t global_item_size0 = ((((abs((int)((arr_size))-0))/(1))/256)+1)*256;
size_t local_item_size0 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern0, 1, NULL,
 &global_item_size0, &local_item_size0, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
	ipmacc_prompt((char*)"IPMACC: memory copyout arr\n");
acc_copyout_and_keep((void*)arr,100000*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory copyout sum\n");
acc_copyout_and_keep((void*)__ipmacc_reduction_array_sum,(((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));

/* second-level reduction on sum */
{
int __kernel_reduction_iterator=0;
{
int bound = (((abs((int)((arr_size))-0))/(1))/256+1)-1;
for(__kernel_reduction_iterator=bound; __kernel_reduction_iterator>0; __kernel_reduction_iterator-=1){
__ipmacc_reduction_array_sum[__kernel_reduction_iterator-1]=__ipmacc_reduction_array_sum[__kernel_reduction_iterator-1]+__ipmacc_reduction_array_sum[__kernel_reduction_iterator];
}
}
}
sum=__ipmacc_reduction_array_sum[0];
free(__ipmacc_reduction_array_sum);
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);



    for (int i = 0; i < arr_size; ++i) {
      sum2 += arr [i];
    }
    cout << "cpu result:" << sum2 << endl;
    cout << "gpu result:" << sum << endl;
    cout << "array size:" << arr_size << endl;
    arr_size++;
    assert(sum == sum2);
  }

  return 0;
}



