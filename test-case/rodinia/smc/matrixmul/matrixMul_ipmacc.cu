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

#include <malloc.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>

#include <math.h>

#define LEN 1024
#define SIZE LEN * LEN

#define TYPE double
#define MIN(a, b)    (a < b ? a : b)


  __global__ void __generated_kernel_region_0(TYPE * a,TYPE * c,TYPE * b);
 
int main(int argc, char *argv[])
{
  int i;
#ifdef __NVCUDA__
  acc_init(acc_device_nvcuda);
#endif
#ifdef __NVOPENCL__
  acc_init(acc_device_nvocl);
#endif

  TYPE *a, *b, *c;
  
  TYPE *seq;
  
  a = (TYPE*)malloc(SIZE * sizeof(TYPE));
  b = (TYPE*)malloc(SIZE * sizeof(TYPE));
  c = (TYPE*)malloc(SIZE * sizeof(TYPE));
  seq = (TYPE*)malloc(SIZE * sizeof(TYPE));

  
  for (i = 0; i < SIZE; ++i) {
    
    a [i] = (TYPE)i;
    b [i] = (TYPE)2 * i;
    c [i] = 0.0f;
  }  

  unsigned long long int tic, toc;
  
  int k, j, l;
  for (k = 0; k < 3; k++) {
    printf("Calculation on GPU ... ");
    tic = clock();



	ipmacc_prompt((char*)"IPMACC: memory allocation c\n");
acc_present_or_create((void*)c,(SIZE+0)*sizeof(TYPE ));
ipmacc_prompt((char*)"IPMACC: memory allocation a\n");
acc_present_or_create((void*)a,(SIZE+0)*sizeof(TYPE ));
ipmacc_prompt((char*)"IPMACC: memory allocation b\n");
acc_present_or_create((void*)b,(SIZE+0)*sizeof(TYPE ));
	ipmacc_prompt((char*)"IPMACC: memory copyin c\n");
acc_pcopyin((void*)c,(SIZE+0)*sizeof(TYPE ));
ipmacc_prompt((char*)"IPMACC: memory copyin a\n");
acc_pcopyin((void*)a,(SIZE+0)*sizeof(TYPE ));
ipmacc_prompt((char*)"IPMACC: memory copyin b\n");
acc_pcopyin((void*)b,(SIZE+0)*sizeof(TYPE ));


{


    {



/* kernel call statement [0, -1]*/
{
dim3 __ipmacc_gridDim(1,1,1);
dim3 __ipmacc_blockDim(1,1,1);
__ipmacc_blockDim.x=16;
__ipmacc_gridDim.x=(((abs((int)((LEN))-(0+0)))/(1))/__ipmacc_blockDim.x)+(((((abs((int)((LEN))-(0+0)))/(1))%(16))==0?0:1));
__ipmacc_blockDim.y=16;
__ipmacc_gridDim.y=(((abs((int)((LEN))-(0+0)))/(1))/__ipmacc_blockDim.y)+(((((abs((int)((LEN))-(0+0)))/(1))%(16))==0?0:1));
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: (%u,%u,%u)\tblockDim: (%u,%u,%u)\n",__ipmacc_gridDim.x,__ipmacc_gridDim.y,__ipmacc_gridDim.z,__ipmacc_blockDim.x,__ipmacc_blockDim.y,__ipmacc_blockDim.z);
__generated_kernel_region_0<<<__ipmacc_gridDim,__ipmacc_blockDim>>>(
(TYPE *)acc_deviceptr((void*)a),
(TYPE *)acc_deviceptr((void*)c),
(TYPE *)acc_deviceptr((void*)b));
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
	ipmacc_prompt((char*)"IPMACC: memory copyout c\n");
acc_copyout_and_keep((void*)c,(SIZE+0)*sizeof(TYPE ));



    toc = clock();
    printf(" %6.4f ms\n", (toc - tic) / (TYPE)1000);
  }

  
  
  
  

  

  printf("Calculation on CPU ... ");

  tic = clock();
  for (i = 0; i < LEN; ++i) {
    for (j = 0; j < LEN; j++) {
      TYPE s = 0;
      for (l = 0; l < LEN; l++) {
        s += a [i * LEN + l] * b [l * LEN + j];
      }
      seq [i * LEN + j] = s;
      if (seq [i * LEN + j] != c [i * LEN + j]) {
        fprintf(stderr, "mismatch on %dx%d\n", i, j);
        exit(-1);
      }
    }
  }
  toc = clock();
  printf(" %6.4f ms\n", (toc - tic) / (TYPE)1000);

  fprintf(stderr, "OpenACC matrix multiply test with dynamic arrays was successful!\n");

  return 0;
}


/*__forceinline__*/ __device__ TYPE  __smc_select_0_a(int index1, int index2, TYPE * g_array, TYPE  s_array[16+0+0][16+0+16], int startptr1, int startptr2, int endptr1, int endptr2, int pitch, int diff1, int diff2){
// the pragmas are well-set. do not check the boundaries.
return s_array[index1-startptr1][index2-startptr2];
}
/*__forceinline__*/ __device__ TYPE  __smc_select_0_b(int index1, int index2, TYPE * g_array, TYPE  s_array[16+0+16][16+0+0], int startptr1, int startptr2, int endptr1, int endptr2, int pitch, int diff1, int diff2){
// the pragmas are well-set. do not check the boundaries.
return s_array[index1-startptr1][index2-startptr2];
}

__device__ void __smc_write_0_a(int index1, int index2, TYPE * g_array, TYPE  s_array[16+0+0][16+0+16], int startptr1, int startptr2, int endptr1, int endptr2, int pitch, TYPE  value){
// the pragmas are well-set. do not check the boundaries.
s_array[index1-startptr1][index2-startptr2]=value;
}
__device__ void __smc_write_0_b(int index1, int index2, TYPE * g_array, TYPE  s_array[16+0+16][16+0+0], int startptr1, int startptr2, int endptr1, int endptr2, int pitch, TYPE  value){
// the pragmas are well-set. do not check the boundaries.
s_array[index1-startptr1][index2-startptr2]=value;
}
 __global__ void __generated_kernel_region_0(TYPE * a,TYPE * c,TYPE * b){
int __kernel_getuid_x=threadIdx.x+blockIdx.x*blockDim.x;
int __kernel_getuid_y=threadIdx.y+blockIdx.y*blockDim.y;
int __kernel_getuid_z=threadIdx.z+blockIdx.z*blockDim.z;
int  i;
int  j;
int  l;

/* declare the shared memory of a */
__shared__ TYPE  __kernel_smc_var_data_a[16+0+0][16+0+16];
/*__shared__*/ int __kernel_smc_startpointer_a;
/*__shared__*/ int __kernel_smc_endpointer_a;
/*__shared__*/ int __kernel_smc_startpointer_a_2d;
/*__shared__*/ int __kernel_smc_endpointer_a_2d;
__kernel_smc_endpointer_a=-1;
__kernel_smc_startpointer_a=-1;
__kernel_smc_endpointer_a_2d=-1;
__kernel_smc_startpointer_a_2d=-1;
/*{
int iterator_of_smc=0;
for(iterator_of_smc=threadIdx.x; iterator_of_smc<(16+0+0); iterator_of_smc+=blockDim.x){
//__kernel_smc_var_data_a[iterator_of_smc]=0;
__kernel_smc_var_tag_a[iterator_of_smc]=0;
}
__syncthreads();
}*/

/* declare the shared memory of b */
__shared__ TYPE  __kernel_smc_var_data_b[16+0+16][16+0+0];
/*__shared__*/ int __kernel_smc_startpointer_b;
/*__shared__*/ int __kernel_smc_endpointer_b;
/*__shared__*/ int __kernel_smc_startpointer_b_2d;
/*__shared__*/ int __kernel_smc_endpointer_b_2d;
__kernel_smc_endpointer_b=-1;
__kernel_smc_startpointer_b=-1;
__kernel_smc_endpointer_b_2d=-1;
__kernel_smc_startpointer_b_2d=-1;
/*{
int iterator_of_smc=0;
for(iterator_of_smc=threadIdx.x; iterator_of_smc<(16+0+16); iterator_of_smc+=blockDim.x){
//__kernel_smc_var_data_b[iterator_of_smc]=0;
__kernel_smc_var_tag_b[iterator_of_smc]=0;
}
__syncthreads();
}*/
{
{


      {
{


        {
 i=0+(__kernel_getuid_y);
if( i < LEN)
{
{


            {
 j=0+(__kernel_getuid_x);
if( j < LEN)
{
                TYPE sum = 0;
for(l = 0; l < LEN; l += 16)
{
                  int offseti = l;
                  int offsetj = l;
//go on with the clause (a[0:LEN:0:LEN:FETCH_CHANNEL:i:0:0:offsetj:0:16:false:0:0:0:0],b[0:LEN:0:LEN:FETCH_CHANNEL:offseti:0:16:j:0:0:false:0:0:0:0])
{ // fetch begins

 // FINDING TILE START
__kernel_smc_startpointer_a=i-0-threadIdx.y;
__kernel_smc_startpointer_a_2d=offsetj-0;

 // FINDING DONE

 // FINDING TILE END
bool lastcol=blockIdx.x==(gridDim.x-1);
bool lastrow=blockIdx.y==(gridDim.y-1);
__kernel_smc_endpointer_a=(lastrow)?LEN-1:blockDim.y+__kernel_smc_startpointer_a+0-1;
__kernel_smc_endpointer_a_2d=(lastcol)?LEN-1:blockDim.x+__kernel_smc_startpointer_a_2d+16-1;
// FINDING DONE
//__fusion_merge_boundary_0()
int __ipmacc_length=__kernel_smc_endpointer_a-__kernel_smc_startpointer_a+1;
int __ipmacc_length_2d=__kernel_smc_endpointer_a_2d-__kernel_smc_startpointer_a_2d+1;
int kk=0,kk2=0;
  kk2=threadIdx.x;
  {
   int idx2=__kernel_smc_startpointer_a_2d+kk2;
   if(idx2<(LEN) && idx2>=(0))
   {
for(kk=threadIdx.y; kk<__ipmacc_length; kk+=blockDim.x)
{
 int idx=__kernel_smc_startpointer_a+kk;
 if(idx<(LEN) && idx>=(0))
 {
__kernel_smc_var_data_a[kk][kk2]=a[idx*LEN+idx2];
//__kernel_smc_var_tag_a[kk][kk2]=1;
//__fusion_merge_fetch_0()
   }
  }
 }
}
__syncthreads();
} // end of fetch
#define a(index) __smc_select_0_a(index, a, __kernel_smc_var_data_a, __kernel_smc_startpointer_a, __kernel_smc_startpointer_a_2d, LEN)

// 1 unique indexes
// [0] i*LEN+m
	#define __ipmacc_smc_index_a_0_dim1 i-__kernel_smc_startpointer_a
	#define __ipmacc_smc_index_a_0_dim2 m-__kernel_smc_startpointer_a_2d
{ // fetch begins

 // FINDING TILE START
__kernel_smc_startpointer_b=offseti-0;
__kernel_smc_startpointer_b_2d=j-0-threadIdx.x;

 // FINDING DONE

 // FINDING TILE END
bool lastcol=blockIdx.x==(gridDim.x-1);
bool lastrow=blockIdx.y==(gridDim.y-1);
__kernel_smc_endpointer_b=(lastrow)?LEN-1:blockDim.y+__kernel_smc_startpointer_b+16-1;
__kernel_smc_endpointer_b_2d=(lastcol)?LEN-1:blockDim.x+__kernel_smc_startpointer_b_2d+0-1;
// FINDING DONE
//__fusion_merge_boundary_2()
int __ipmacc_length=__kernel_smc_endpointer_b-__kernel_smc_startpointer_b+1;
int __ipmacc_length_2d=__kernel_smc_endpointer_b_2d-__kernel_smc_startpointer_b_2d+1;
int kk=0,kk2=0;
  for(kk2=threadIdx.x; kk2<__ipmacc_length_2d; kk2+=blockDim.y)
  {
   int idx2=__kernel_smc_startpointer_b_2d+kk2;
   if(idx2<(LEN) && idx2>=(0))
   {
  kk=threadIdx.y;
{
 int idx=__kernel_smc_startpointer_b+kk;
 if(idx<(LEN) && idx>=(0))
 {
__kernel_smc_var_data_b[kk][kk2]=b[idx*LEN+idx2];
//__kernel_smc_var_tag_b[kk][kk2]=1;
//__fusion_merge_fetch_2()
   }
  }
 }
}
__syncthreads();
} // end of fetch
#define b(index) __smc_select_0_b(index, b, __kernel_smc_var_data_b, __kernel_smc_startpointer_b, __kernel_smc_startpointer_b_2d, LEN)

// 1 unique indexes
// [0] m*LEN+j
	#define __ipmacc_smc_index_b_0_dim1 m-__kernel_smc_startpointer_b
	#define __ipmacc_smc_index_b_0_dim2 j-__kernel_smc_startpointer_b_2d

{


                  {
                    if (j < LEN && i < LEN) {
                      int m;
for(m = l; m < MIN(l + 16, LEN); m++)
{
                        sum += __kernel_smc_var_data_a[__ipmacc_smc_index_a_0_dim1][__ipmacc_smc_index_a_0_dim2] /* replacing a [i * LEN + m]*/  * __kernel_smc_var_data_b[__ipmacc_smc_index_b_0_dim1][__ipmacc_smc_index_b_0_dim2] /* replacing b [m * LEN + j]*/ ;
                      }
}
                  }
}
#undef a
#undef b

//end up with the clause (a[0:LEN:0:LEN:FETCH_CHANNEL:i:0:0:offsetj:0:16:false:0:0:0:0],b[0:LEN:0:LEN:FETCH_CHANNEL:offseti:0:16:j:0:0:false:0:0:0:0])
}
if (j < LEN && i < LEN) {
                  c [i * LEN + j] = sum;
                }
              }

}
}
}

}
}
}
}
}
//append writeback of scalar variables
}

