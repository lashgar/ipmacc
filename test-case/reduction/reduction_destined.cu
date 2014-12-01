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

using namespace std;


__global__ void __generated_kernel_region_0(int* arr,int arr_size,int* sum__ipmacc_reductionarray_internal);

int main()
{
#define SIZE 100000
	int arr [SIZE];
	int sum = 0;
	int sum2 = 0;
	int arr_size = 5400;

	srand(time(NULL));

	while (arr_size < 10000) {
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
		int dimGrid=(((abs((int)((arr_size))-0))/(1)))/256+1;
		if(__ipmacc_reduction_array_sum==NULL){
			__ipmacc_reduction_array_sum=(int*)malloc(dimGrid*sizeof(int));
			//__ipmacc_reduction_array_sum=(int*)malloc((((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));
			//for(int kk=0; kk<(((abs((int)((arr_size))-0))/(1))/256+1); kk++){
			//	__ipmacc_reduction_array_sum[kk]=-1;
			//}
			acc_create((void*)__ipmacc_reduction_array_sum,(((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));
			//acc_copyin((void*)__ipmacc_reduction_array_sum,(((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));
		}

		/* kernel call statement [0]*/
		//cout << "array size:" << arr_size << endl;
		assert((int*)acc_deviceptr((void*)arr));
		assert((int*)acc_deviceptr((void*)__ipmacc_reduction_array_sum));
		int dimBlock=256;
		//printf("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",dimGrid,dimBlock);
		__generated_kernel_region_0<<<dimGrid,dimBlock>>>(
				(int*)acc_deviceptr((void*)arr),
				arr_size,
				(int*)acc_deviceptr((void*)__ipmacc_reduction_array_sum));
		cudaDeviceSynchronize();
		//cout<<"Error> "<<cudaGetErrorString(cudaPeekAtLastError())<<endl;
		/* kernel call statement*/
		ipmacc_prompt((char*)"IPMACC: memory copyout arr\n");
		acc_copyout_and_keep((void*)arr,100000*sizeof(int));
		ipmacc_prompt((char*)"IPMACC: memory copyout sum\n");
		acc_copyout_and_keep((void*)__ipmacc_reduction_array_sum,(((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));

		/* second-level reduction on sum */
		{
			for(int kk=0; kk<dimGrid; kk++){
				printf("\t%d\n",__ipmacc_reduction_array_sum[kk]);
			}
			acc_create((void*)__ipmacc_reduction_array_sum,(((abs((int)((arr_size))-0))/(1))/256+1)*sizeof(int));
			int __kernel_reduction_iterator=0;
			int count= (((abs((int)((arr_size))-0))/(1))%256) == 0? (((abs((int)((arr_size))-0))/(1))/256+1)-2: (((abs((int)((arr_size))-0))/(1))/256+1)-1;
			for(__kernel_reduction_iterator=count; __kernel_reduction_iterator>0; __kernel_reduction_iterator-=1){
			//for(__kernel_reduction_iterator=(((abs((int)((arr_size))-0))/(1))/256+1)-1; __kernel_reduction_iterator>0; __kernel_reduction_iterator-=1){
				__ipmacc_reduction_array_sum[__kernel_reduction_iterator-1]=__ipmacc_reduction_array_sum[__kernel_reduction_iterator-1]+__ipmacc_reduction_array_sum[__kernel_reduction_iterator];
			}
		}
		sum=__ipmacc_reduction_array_sum[0];
		if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
		cudaDeviceSynchronize();



		for (int i = 0; i < arr_size; ++i) {
			sum2 += arr [i];
		}
		cout << "cpu result:" << sum2 << endl;
		cout << "gpu result:" << sum << endl;
		cout << "array size:" << arr_size << endl;
		cout << "===================" << endl;
		arr_size++;
		assert(sum == sum2);
	}

	return 0;
}


__global__ void __generated_kernel_region_0(int* arr,int arr_size,int* sum__ipmacc_reductionarray_internal){
	int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
	__shared__ int __kernel_reduction_shmem_int[256];
	__kernel_reduction_shmem_int[threadIdx.x]=0;
	int __kernel_reduction_iterator=0;
	int sum;
	{
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
						__kernel_reduction_shmem_int[threadIdx.x]=sum;//threadIdx.x;//;
						__syncthreads();
						
					//	   for(__kernel_reduction_iterator=256; __kernel_reduction_iterator>1; __kernel_reduction_iterator=__kernel_reduction_iterator/2){
					//	   if(threadIdx.x<__kernel_reduction_iterator && threadIdx.x>=__kernel_reduction_iterator/2){
					//	   __kernel_reduction_shmem_int[threadIdx.x-(__kernel_reduction_iterator/2)]=__kernel_reduction_shmem_int[threadIdx.x-(__kernel_reduction_iterator/2)]+__kernel_reduction_shmem_int[threadIdx.x];
					//	   }
					//	   __syncthreads();
					//	   }
						 
						for (unsigned int s=blockDim.x/2; s>0; s>>=1) {
							if(threadIdx.x<s)
							{
								__kernel_reduction_shmem_int[threadIdx.x] += __kernel_reduction_shmem_int[threadIdx.x + s];
							}
							__syncthreads();
						}
					}// the end of sum scope
					if(threadIdx.x==0){
						//int tot_sum=0;
						//for (int s=0; s<(int)blockDim.x; s++) {
						//	tot_sum+=arr[s];//__kernel_reduction_shmem_int[s];
						//}
						//sum__ipmacc_reductionarray_internal[blockIdx.x]=tot_sum;//threadIdx.x+1;
						sum__ipmacc_reductionarray_internal[blockIdx.x]=__kernel_reduction_shmem_int[0];
					}

				} // closed for reduction-end

			}
		}
	}
}

