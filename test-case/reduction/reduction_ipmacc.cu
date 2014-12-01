#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#include <cuda.h>

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include <iostream>
#include "openacc.h"

using namespace std;


  __global__ void __generated_kernel_region_0(int* arr,int arr_size,int* sum__ipmacc_reductionarray_internal);
 
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

/* kernel call statement [0]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",(((abs((int)((arr_size))-0))/(1)))/256+1,256);
__generated_kernel_region_0<<<(((abs((int)((arr_size))-0))/(1)))/256+1,256>>>(
(int*)acc_deviceptr((void*)arr),
arr_size,
(int*)acc_deviceptr((void*)__ipmacc_reduction_array_sum));
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
cudaDeviceSynchronize();



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


 __global__ void __generated_kernel_region_0(int* arr,int arr_size,int* sum__ipmacc_reductionarray_internal){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
__shared__ int __kernel_reduction_shmem_int[256];
int __kernel_reduction_iterator=0;
int sum;{
{
{
int i=0+(__kernel_getuid);
if( i < arr_size)
{ //opened for private and reduction
/*private:+:sum*/
{ //start of reduction region for sum 
int sum=0;

{
      sum += arr [i];
    }
/*reduction:+:sum*/

/* reduction on sum */
__syncthreads();
__kernel_reduction_shmem_int[threadIdx.x]=sum;
__syncthreads();
for(__kernel_reduction_iterator=blockDim.x/2;__kernel_reduction_iterator>0; __kernel_reduction_iterator>>=1) {
if(threadIdx.x<__kernel_reduction_iterator){
__kernel_reduction_shmem_int[threadIdx.x]=__kernel_reduction_shmem_int[threadIdx.x]+__kernel_reduction_shmem_int[threadIdx.x+__kernel_reduction_iterator];
}
__syncthreads();
}
}// the end of sum scope
if(threadIdx.x==0){
sum__ipmacc_reductionarray_internal[blockIdx.x]=__kernel_reduction_shmem_int[0];
}

} // closed for reduction-end

}
}
}
}

