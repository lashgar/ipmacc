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

#include <cuda.h>





extern int dataN;
extern int kernelN;

  __global__ void __generated_kernel_region_0(float * h_Kernel,float * h_Data,float * h_Result,const int  kernelNL,const int  dataNL);
 
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

/* kernel call statement [0]*/
{
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",(((abs((int)((dataNL))-0))/(1)))/256+(((((abs((int)((dataNL))-0))/(1)))%(256))==0?0:1),256);
__generated_kernel_region_0<<<(((abs((int)((dataNL))-0))/(1)))/256+(((((abs((int)((dataNL))-0))/(1)))%(256))==0?0:1),256>>>(
(float *)acc_deviceptr((void*)h_Kernel),
(float *)acc_deviceptr((void*)h_Data),
(float *)acc_deviceptr((void*)h_Result),
kernelNL,
dataNL);
}
/* kernel call statement*/
	ipmacc_prompt((char*)"IPMACC: memory copyout h_Result\n");
acc_copyout_and_keep((void*)h_Result,(dataN+0)*sizeof(float ));
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
{
cudaError err=cudaDeviceSynchronize();
if(err!=cudaSuccess){
printf("Kernel Launch Error! error code (%d)\n",err);
assert(0&&"Launch Failure!\n");}
}



}




  __global__ void __generated_kernel_region_1(int  stride,int  base,float * h_Output);
 
  __global__ void __generated_kernel_region_2(const int  N,int  stride,int  base,float * h_Output);
 
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

/* kernel call statement [1, 2]*/
{
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 1 > gridDim: %d\tblockDim: %d\n",(((abs((int)((stride))-0))/(1)))/256+(((((abs((int)((stride))-0))/(1)))%(256))==0?0:1),256);
__generated_kernel_region_1<<<(((abs((int)((stride))-0))/(1)))/256+(((((abs((int)((stride))-0))/(1)))%(256))==0?0:1),256>>>(
stride,
base,
(float *)acc_deviceptr((void*)h_Output));
}
/* kernel call statement*/
				if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
{
cudaError err=cudaDeviceSynchronize();
if(err!=cudaSuccess){
printf("Kernel Launch Error! error code (%d)\n",err);
assert(0&&"Launch Failure!\n");}
}



        }
      }


    }else{
            

						ipmacc_prompt((char*)"IPMACC: memory getting device pointer for h_Output\n");
acc_present((void*)h_Output);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for h_Input\n");
acc_present((void*)h_Input);

/* kernel call statement [1, 3]*/
{
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 2 > gridDim: %d\tblockDim: %d\n",(((abs((int)((((N/(2*stride))+1)))-0))/(1)))/256+(((((abs((int)((((N/(2*stride))+1)))-0))/(1)))%(256))==0?0:1),256);
__generated_kernel_region_2<<<(((abs((int)((((N/(2*stride))+1)))-0))/(1)))/256+(((((abs((int)((((N/(2*stride))+1)))-0))/(1)))%(256))==0?0:1),256>>>(
N,
stride,
base,
(float *)acc_deviceptr((void*)h_Output));
}
/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
{
cudaError err=cudaDeviceSynchronize();
if(err!=cudaSuccess){
printf("Kernel Launch Error! error code (%d)\n",err);
assert(0&&"Launch Failure!\n");}
}



    }
  }


}
	ipmacc_prompt((char*)"IPMACC: memory copyout h_Output\n");
acc_copyout_and_keep((void*)h_Output,(dataN+0)*sizeof(float ));



}



 __global__ void __generated_kernel_region_0(float * h_Kernel,float * h_Data,float * h_Result,const int  kernelNL,const int  dataNL){
int __kernel_getuid_x=threadIdx.x+blockIdx.x*blockDim.x;
int __kernel_getuid_y=threadIdx.y+blockIdx.y*blockDim.y;
int __kernel_getuid_z=threadIdx.z+blockIdx.z*blockDim.z;
{
{
{
int i=0+(__kernel_getuid_x);
if( i < dataNL)
{
    double sum = 0;
for(int j = 0; j < kernelNL; j++)
{
      sum += h_Data [i ^ j] * h_Kernel [j];
    }
h_Result [i] = (float)sum;
  }

}
}
}
}

 __global__ void __generated_kernel_region_1(int  stride,int  base,float * h_Output){
int __kernel_getuid_x=threadIdx.x+blockIdx.x*blockDim.x;
int __kernel_getuid_y=threadIdx.y+blockIdx.y*blockDim.y;
int __kernel_getuid_z=threadIdx.z+blockIdx.z*blockDim.z;
{
{
{
int j=0+(__kernel_getuid_x);
if( j < stride)
{
            
            int i0 = base + j + 0;
            int i1 = base + j + stride;

            float T1 = h_Output [i0];
            float T2 = h_Output [i1];
            h_Output [i0] = T1 + T2;
            h_Output [i1] = T1 - T2;
          }

}
}
}
}

 __global__ void __generated_kernel_region_2(const int  N,int  stride,int  base,float * h_Output){
int __kernel_getuid_x=threadIdx.x+blockIdx.x*blockDim.x;
int __kernel_getuid_y=threadIdx.y+blockIdx.y*blockDim.y;
int __kernel_getuid_z=threadIdx.z+blockIdx.z*blockDim.z;
int  baseI;
{
{
{
 baseI=0+(__kernel_getuid_x);
if( baseI < (N / (2 * stride) + 1))
{
        
        base = baseI * 2 * stride;
        if (base < N) {
for(int j = 0; j < stride; j++)
{
            
            int i0 = base + j + 0;
            int i1 = base + j + stride;

            float T1 = h_Output [i0];
            float T2 = h_Output [i1];
            h_Output [i0] = T1 + T2;
            h_Output [i1] = T1 - T2;
          }
}
      }

}
}
}
}

