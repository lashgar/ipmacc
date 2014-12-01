
#include <stdio.h>

#define SIZE 1000
#define NTHREAD 256
#define blockDim NTHREAD


int main(){
	int __kernel_reduction_shmem_int[SIZE];
	for(int i=0; i<NTHREAD; i++){
		__kernel_reduction_shmem_int[i]=i;
	}
	for (unsigned int s=blockDim/2; s>0; s>>=1) {
		for(int threadIdx=0; threadIdx<NTHREAD; threadIdx++){
			if (threadIdx < s) {
				__kernel_reduction_shmem_int[threadIdx] += __kernel_reduction_shmem_int[threadIdx + s];
			}
		}
	}
	printf("sum> %d\n",__kernel_reduction_shmem_int[0]);
	return 0;
}
