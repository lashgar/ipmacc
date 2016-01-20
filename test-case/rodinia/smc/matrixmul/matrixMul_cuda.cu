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

//#define LEN 1024
#define SIZE LEN * LEN

#define TYPE double
#define MIN(a, b)    (a < b ? a : b)


__global__ void __generated_kernel_region_0(TYPE * a,TYPE * c,TYPE * b, int LEN);

int main(int argc, char *argv[])
{
    int i;
#ifdef __NVCUDA__
    acc_init(acc_device_nvcuda);
#endif
#ifdef __NVOPENCL__
    acc_init(acc_device_nvocl);
#endif

    int LEN = -1;
    if(argc!=2){
        printf("usage: ./matMul <size>\n");
        exit(-1);
    }else{
        sscanf(argv[1], "%d", &LEN);
    }
    assert(LEN>0);



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
                            (TYPE *)acc_deviceptr((void*)b),
                            LEN);
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







    /*
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
    */
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
__global__ void __generated_kernel_region_0(TYPE * a,TYPE * c,TYPE * b, int LEN){
    int __kernel_getuid_x=threadIdx.x+blockIdx.x*blockDim.x;
    int __kernel_getuid_y=threadIdx.y+blockIdx.y*blockDim.y;
    int __kernel_getuid_z=threadIdx.z+blockIdx.z*blockDim.z;
    int  i;
    int  j;
    int  l;

    /* declare the shared memory of a */
    __shared__ TYPE  __kernel_smc_var_data_a[16][16];
    __shared__ TYPE  __kernel_smc_var_data_b[16][16];
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
                        {
                            __syncthreads();
                            {
                                int idx2 = offsetj + threadIdx.x;
                                int idx  = i - threadIdx.y + threadIdx.y;
                                __kernel_smc_var_data_a[threadIdx.y][threadIdx.x]=a[idx*LEN+idx2];
                            }
                            {
                                int idx  = offseti + threadIdx.y;
                                int idx2 = j - threadIdx.x + threadIdx.x;
                                __kernel_smc_var_data_b[threadIdx.y][threadIdx.x]=b[idx*LEN+idx2];
                            }
                            __syncthreads();

                            {
                                int m;
                                //for(m = l; m < MIN(l + 16, LEN); m++)
                                for(m = 0; m < 16; m++)
                                {
                                    sum += __kernel_smc_var_data_a[threadIdx.y][m] /* replacing a [i * LEN + m]*/  * __kernel_smc_var_data_b[m][threadIdx.x] /* replacing b [m * LEN + j]*/ ;
                                }
                            }
                        }

                        //end up with the clause (a[0:LEN:0:LEN:FETCH_CHANNEL:i:0:0:offsetj:0:16:false:0:0:0:0],b[0:LEN:0:LEN:FETCH_CHANNEL:offseti:0:16:j:0:0:false:0:0:0:0])
                    }
                    if (j < LEN && i < LEN) {
                        c [i * LEN + j] = sum;
                    }
                }
            }
        }
    }
    //append writeback of scalar variables
}

