#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#ifdef __cplusplus
#include "openacc_container.h"
#endif

#include <CL/cl.h>
extern cl_int __ipmacc_clerr ;
extern cl_context __ipmacc_clctx ;
extern size_t __ipmacc_parmsz;
extern cl_device_id* __ipmacc_cldevs;
extern cl_command_queue __ipmacc_command_queue;
extern cl_command_queue __ipmacc_temp_cmdqueue;






extern int dataN;
extern int kernelN;

void dyadicConvolutionCPU_openacc(
  float *h_Result_f,
  float *h_Data_f,
  float *h_Kernel_f,
  int log2dataN,
  int log2kernelN)
{
  
  
  const int dataNL = 1 << log2dataN;
  const int kernelNL = 1 << log2kernelN;

  float *h_Result = (float*)h_Result_f;
  float *h_Data = (float*)h_Data_f;
  float *h_Kernel = (float*)h_Kernel_f;

    

	ipmacc_prompt((char*)"IPMACC: memory allocation h_Result\n");
acc_present_or_create((void*)h_Result,(dataN+0)*sizeof(float ));
ipmacc_prompt((char*)"IPMACC: memory allocation h_Data\n");
acc_present_or_create((void*)h_Data,(dataN+0)*sizeof(float ));
ipmacc_prompt((char*)"IPMACC: memory allocation h_Kernel\n");
acc_present_or_create((void*)h_Kernel,(kernelN+0)*sizeof(float ));
	ipmacc_prompt((char*)"IPMACC: memory copyin h_Data\n");
acc_pcopyin((void*)h_Data,(dataN+0)*sizeof(float ));
ipmacc_prompt((char*)"IPMACC: memory copyin h_Kernel\n");
acc_pcopyin((void*)h_Kernel,(kernelN+0)*sizeof(float ));

/* kernel call statement*/
static cl_kernel __ipmacc_clkern0=NULL;
const char* kernelSource0 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n\n__kernel void __generated_kernel_region_0(__global float * h_Kernel,__global float * h_Data,__global float * h_Result,const int kernelNL,const int dataNL){\nint __kernel_getuid_x=get_global_id(0);\nint __kernel_getuid_y=get_global_id(1);\nint __kernel_getuid_z=get_global_id(2);\n{\n{\n{\nint i=0+(__kernel_getuid_x);\nif( i < dataNL)\n{\n    double sum = 0;\nfor(int j = 0; j < kernelNL; j++)\n{\n      sum += h_Data [i ^ j] * h_Kernel [j];\n    }\nh_Result [i] = (float)sum;\n  }\n\n}\n}\n}\n}";
__ipmacc_clkern0=(cl_kernel)acc_training_kernel_add(kernelSource0, (char*)" ", (char*)"__generated_kernel_region_0",4225418, 5);
{
cl_mem ptr=(cl_mem)acc_deviceptr(h_Kernel);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(h_Data);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 1, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(h_Result);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 2, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
const int  immediate=kernelNL;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 3, sizeof(const int ), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
const int  immediate=dataNL;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 4, sizeof(const int ), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",((((abs((int)((dataNL))-0))/(1)))/256+(((((abs((int)((dataNL))-0))/(1)))%(256))==0?0:1))*256,256);
size_t global_item_size0 = ((((abs((int)((dataNL))-0))/(1)))/256+(((((abs((int)((dataNL))-0))/(1)))%(256))==0?0:1))*256;
size_t local_item_size0 = 256;
__ipmacc_temp_cmdqueue=(cl_command_queue)acc_training_decide_command_queue(4225418);
acc_training_kernel_start(4225418);
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_temp_cmdqueue, __ipmacc_clkern0, 1, NULL,
 &global_item_size0, &local_item_size0, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
	ipmacc_prompt((char*)"IPMACC: memory copyout h_Result\n");
acc_copyout_and_keep((void*)h_Result,(dataN+0)*sizeof(float ));
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFinish(__ipmacc_temp_cmdqueue);
acc_training_kernel_end();



}




void fwtCPU_openacc(float *h_Output_f, float *h_Input_f, int log2N)
{
  const int N = 1 << log2N;
  float *h_Output = (float*)h_Output_f;
  float *h_Input = (float*)h_Input_f;

  for (int pos = 0; pos < N; pos++) {
    h_Output [pos] = h_Input [pos];
  }

  int stride, baseI, base;
  
    

	ipmacc_prompt((char*)"IPMACC: memory allocation h_Output\n");
acc_present_or_create((void*)h_Output,(dataN+0)*sizeof(float ));
ipmacc_prompt((char*)"IPMACC: memory allocation h_Input\n");
acc_present_or_create((void*)h_Input,(dataN+0)*sizeof(float ));
	ipmacc_prompt((char*)"IPMACC: memory copyin h_Input\n");
acc_pcopyin((void*)h_Input,(dataN+0)*sizeof(float ));


{


  
		for(stride = N / 2; stride >= 1; stride >>= 1)
 {
    printf("calling %d\n", stride);
    
    if (stride > 128) {
      
			for(baseI = 0; baseI < (N / (2 * stride) + 1); baseI++)
 {
        
        base = baseI * 2 * stride;
        if (base < N) {
                    

								ipmacc_prompt((char*)"IPMACC: memory getting device pointer for h_Output\n");
acc_present((void*)h_Output);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for h_Input\n");
acc_present((void*)h_Input);

/* kernel call statement*/
static cl_kernel __ipmacc_clkern1=NULL;
const char* kernelSource1 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n\n__kernel void __generated_kernel_region_1(int stride,int base,__global float * h_Output){\nint __kernel_getuid_x=get_global_id(0);\nint __kernel_getuid_y=get_global_id(1);\nint __kernel_getuid_z=get_global_id(2);\n{\n{\n{\nint j=0+(__kernel_getuid_x);\nif( j < stride)\n{\n\n            int i0 = base + j + 0;\n            int i1 = base + j + stride;\n\n            float T1 = h_Output [i0];\n            float T2 = h_Output [i1];\n            h_Output [i0] = T1 + T2;\n            h_Output [i1] = T1 - T2;\n          }\n\n}\n}\n}\n}";
__ipmacc_clkern1=(cl_kernel)acc_training_kernel_add(kernelSource1, (char*)" ", (char*)"__generated_kernel_region_1",6804576, 3);
{
int  immediate=stride;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern1, 0, sizeof(int ), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
int  immediate=base;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern1, 1, sizeof(int ), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(h_Output);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern1, 2, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 1 > gridDim: %d\tblockDim: %d\n",((((abs((int)((stride))-0))/(1)))/256+(((((abs((int)((stride))-0))/(1)))%(256))==0?0:1))*256,256);
size_t global_item_size1 = ((((abs((int)((stride))-0))/(1)))/256+(((((abs((int)((stride))-0))/(1)))%(256))==0?0:1))*256;
size_t local_item_size1 = 256;
__ipmacc_temp_cmdqueue=(cl_command_queue)acc_training_decide_command_queue(6804576);
acc_training_kernel_start(6804576);
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_temp_cmdqueue, __ipmacc_clkern1, 1, NULL,
 &global_item_size1, &local_item_size1, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
				if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFinish(__ipmacc_temp_cmdqueue);
acc_training_kernel_end();



        }
      }


    }else{
            

						ipmacc_prompt((char*)"IPMACC: memory getting device pointer for h_Output\n");
acc_present((void*)h_Output);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for h_Input\n");
acc_present((void*)h_Input);

/* kernel call statement*/
static cl_kernel __ipmacc_clkern2=NULL;
const char* kernelSource2 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n\n__kernel void __generated_kernel_region_2(const int N,int stride,int base,__global float * h_Output){\nint __kernel_getuid_x=get_global_id(0);\nint __kernel_getuid_y=get_global_id(1);\nint __kernel_getuid_z=get_global_id(2);\nint baseI;\n{\n{\n{\n baseI=0+(__kernel_getuid_x);\nif( baseI < (N / (2 * stride) + 1))\n{\n\n        base = baseI * 2 * stride;\n        if (base < N) {\nfor(int j = 0; j < stride; j++)\n{\n\n            int i0 = base + j + 0;\n            int i1 = base + j + stride;\n\n            float T1 = h_Output [i0];\n            float T2 = h_Output [i1];\n            h_Output [i0] = T1 + T2;\n            h_Output [i1] = T1 - T2;\n          }\n}\n      }\n\n}\n}\n}\n}";
__ipmacc_clkern2=(cl_kernel)acc_training_kernel_add(kernelSource2, (char*)" ", (char*)"__generated_kernel_region_2",3452636, 4);
{
const int  immediate=N;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 0, sizeof(const int ), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
int  immediate=stride;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 1, sizeof(int ), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
int  immediate=base;
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 2, sizeof(int ), (void *)&immediate);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(h_Output);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 3, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 2 > gridDim: %d\tblockDim: %d\n",((((abs((int)((((N/(2*stride))+1)))-0))/(1)))/256+(((((abs((int)((((N/(2*stride))+1)))-0))/(1)))%(256))==0?0:1))*256,256);
size_t global_item_size2 = ((((abs((int)((((N/(2*stride))+1)))-0))/(1)))/256+(((((abs((int)((((N/(2*stride))+1)))-0))/(1)))%(256))==0?0:1))*256;
size_t local_item_size2 = 256;
__ipmacc_temp_cmdqueue=(cl_command_queue)acc_training_decide_command_queue(3452636);
acc_training_kernel_start(3452636);
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_temp_cmdqueue, __ipmacc_clkern2, 1, NULL,
 &global_item_size2, &local_item_size2, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFinish(__ipmacc_temp_cmdqueue);
acc_training_kernel_end();



    }
  }


}
	ipmacc_prompt((char*)"IPMACC: memory copyout h_Output\n");
acc_copyout_and_keep((void*)h_Output,(dataN+0)*sizeof(float ));



}



