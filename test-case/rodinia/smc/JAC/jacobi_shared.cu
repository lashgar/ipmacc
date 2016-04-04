#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#include <cuda.h>
#include <assert.h>
#include <openacc.h>
#include <math.h>

#if defined(_WIN32) || defined(_WIN64)
#include <sys/timeb.h>
#define gettime(a) _ftime(a)
#define usec(t1, t2) ((((t2).time - (t1).time) * 1000 + ((t2).millitm - (t1).millitm)) * 100)
typedef struct _timeb timestruct;
#else
#include <sys/time.h>
#define gettime(a) gettimeofday(a, NULL)
#define usec(t1, t2) (((t2).tv_sec - (t1).tv_sec) * 1000000 + ((t2).tv_usec - (t1).tv_usec))
typedef struct timeval timestruct;
#endif

#define IN_RANGE(x, min, max)   ((x)>=(min) && (x)<=(max))

__global__ void __generated_kernel_region_0(float * a,int  m,int  n,float * b,float  w2,float  w1,float  w0);

void smooth(float* a, float* b, float w0, float w1, float w2, int n, int m, int niters)
{
    int i, j, iter;;;
    float* tmp;
    for (iter = 1; iter <= niters; ++iter) {


        acc_create((void*)a,(n*m+0)*sizeof(float ));
        acc_create((void*)b,(n*m+0)*sizeof(float ));
        acc_copyin((void*)a,(n*m+0)*sizeof(float ));
        acc_copyin((void*)b,(n*m+0)*sizeof(float ));

        /* kernel call statement [0]*/
        {
            dim3 __ipmacc_gridDim(1,1,1);
            dim3 __ipmacc_blockDim(1,1,1);
            __ipmacc_blockDim.x=16;
            __ipmacc_gridDim.x=(((abs((int)(((m-1)))-(1+0)))/(1))/__ipmacc_blockDim.x)+(((((abs((int)(((m-1)))-(1+0)))/(1))%(16))==0?0:1));
            __ipmacc_blockDim.y=16;
            __ipmacc_gridDim.y=(((abs((int)(((n-1)))-(1+0)))/(1))/__ipmacc_blockDim.y)+(((((abs((int)(((n-1)))-(1+0)))/(1))%(16))==0?0:1));
            if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: (%u,%u,%u)\tblockDim: (%u,%u,%u)\n",__ipmacc_gridDim.x,__ipmacc_gridDim.y,__ipmacc_gridDim.z,__ipmacc_blockDim.x,__ipmacc_blockDim.y,__ipmacc_blockDim.z);


            int borderCols = 1;
            int borderRows = 1;
            int smallBlockCol = 16-2;
            int smallBlockRow = 16-2;
            int blockCols = m/smallBlockCol+((m%smallBlockCol==0)?0:1);
            int blockRows = n/smallBlockRow+((n%smallBlockRow==0)?0:1);
            dim3 gridDimen(blockRows, blockCols);


            __generated_kernel_region_0<<<gridDimen,__ipmacc_blockDim>>>(
                    (float *)acc_deviceptr((void*)a),
                    m,
                    n,
                    (float *)acc_deviceptr((void*)b),
                    w2,
                    w1,
                    w0);
        }
        /* kernel call statement*/
        acc_copyout_and_keep((void*)a,(n*m+0)*sizeof(float ));
        {
            cudaError err=cudaDeviceSynchronize();
            if(err!=cudaSuccess){
                printf("Kernel Launch Error! error code (%d)\n",err);
                exit(-1);
            }
        }

        tmp = a;  a = b;  b = tmp;
    }
}

void smoothhost(float* a, float* b, float w0, float w1, float w2, int n, int m, int niters)
{
    int i, j, iter;;;
    float* tmp;
    for (iter = 1; iter <= niters; ++iter) {
        for (i = 1; i < n - 1; ++i) {
            for (j = 1; j < m - 1; ++j) {
                a [i * m + j] = w0 * b [i * m + j] +
                    w1 * (b [(i - 1) * m + j] + b [(i + 1) * m + j] + b [i * m + j - 1] + b [i * m + j + 1]) +
                    w2 * (b [(i - 1) * m + j - 1] + b [(i - 1) * m + j + 1] + b [(i + 1) * m + j - 1] + b [(i + 1) * m + j + 1]);
            }
        }
        tmp = a;  a = b;  b = tmp;
    }
}

void doprt(char* s, float* a, float* ah, int i, int j, int n, int m)
{
    printf("%s[%d][%d] = %g  =  %g\n", s, i, j, a [i * m + j], ah [i * m + j]);
}

int main(int argc, char* argv[])
{
    float *aa, *bb, *aahost, *bbhost;;;;
    int i, j;;
    float w0, w1, w2;;;
    int n, m, aerrs, berrs, iters;;;;
    float dif, rdif, tol;;;
    timestruct t1, t2, t3;;;
    long long cgpu, chost;;

    n = 1024;
    m = 1024;
    iters = 1;

    if( argc > 1 ){
        n = atoi( argv[1] );
        if( argc > 2 ){
            m = atoi( argv[2] );
            if( argc > 3 ){
                iters = atoi( argv[3] );
            }
        }
    }


    if (n <= 0) {
        n = 1000;
    }
    if (m <= 0) {
        m = n;
    }
    if (iters <= 0) {
        iters = 10;
    }

    aa = (float*)malloc(sizeof(float) * n * m);
    aahost = (float*)malloc(sizeof(float) * n * m);
    bb = (float*)malloc(sizeof(float) * n * m);
    bbhost = (float*)malloc(sizeof(float) * n * m);
    for (i = 0; i < n; ++i) {
        for (j = 0; j < m; ++j) {
            aa [i * m + j] = 0;
            aahost [i * m + j] = 0;
            bb [i * m + j] = i * 1000 + j;
            bbhost [i * m + j] = i * 1000 + j;
        }
    }
    w0 = 0.5;
    w1 = 0.3;
    w2 = 0.2;
    gettime(&t1);
    smooth(aa, bb, w0, w1, w2, n, m, iters);
    gettime(&t2);
    smoothhost(aahost, bbhost, w0, w1, w2, n, m, iters);
    gettime(&t3);

    cgpu = usec(t1, t2);
    chost = usec(t2, t3);

    printf("matrix %d x %d, %d iterations\n", n, m, iters);
    printf("%13ld microseconds optimized\n", cgpu);
    printf("%13ld microseconds on host\n", chost);

    aerrs = berrs = 0;
    tol = 0.000005;
    for (i = 0; i < n; ++i) {
        for (j = 0; j < m; ++j) {
            rdif = dif = fabsf(aa [i * m + j] - aahost [i * m + j]);
            if (aahost [i * m + j]) {
                rdif = fabsf(dif / aahost [i * m + j]);
            }
            if (rdif > tol) {
                ++aerrs;
                if (aerrs < 10) {
                    printf("aa[%d][%d] = %12.7e != %12.7e, dif=%12.7e\n", i, j, (double)aa [i * m + j], (double)aahost [i * m + j], (double)dif);
                }
            }
            rdif = dif = fabsf(bb [i * m + j] - bbhost [i * m + j]);
            if (bbhost [i * m + j]) {
                rdif = fabsf(dif / bbhost [i * m + j]);
            }
            if (rdif > tol) {
                ++berrs;
                if (berrs < 10) {
                    printf("bb[%d][%d] = %12.7e != %12.7e, dif=%12.7e\n", i, j, (double)bb [i * m + j], (double)bbhost [i * m + j], (double)dif);
                }
            }
        }
    }
    if (aerrs == 0 && berrs == 0) {
        fprintf(stderr, "no errors found\n");
        return 0;
    }else{
        fprintf(stderr, "%d ERRORS found\n", aerrs + berrs);
        return 1;
    }
}



__global__ void __generated_kernel_region_0(float * a,int  m,int  n,float * b,float  w2,float  w1,float  w0){
    int __kernel_getuid_x=threadIdx.x+blockIdx.x*blockDim.x;
    int __kernel_getuid_y=threadIdx.y+blockIdx.y*blockDim.y;
    int  i;
    int  j;

    __shared__ float btile[16+2][16+2];

    int bx = blockIdx.x;
    int by = blockIdx.y;

    int tx=threadIdx.x;
    int ty=threadIdx.y;


    // each block finally computes result for a small block
    // after N iterations. 
    // it is the non-overlapping small blocks that cover 
    // all the input data

    // calculate the small block size
    int iteration=1;
    int small_block_rows = 16-iteration*2;//EXPAND_RATE
    int small_block_cols = 16-iteration*2;//EXPAND_RATE

    // calculate the boundary for the block according to 
    // the boundary of its small block
    int blkY = small_block_rows*by-iteration;
    int blkX = small_block_cols*bx-iteration;
    int blkYmax = blkY+16-1;
    int blkXmax = blkX+16-1;

    // calculate the global thread coordination
    int yidx = blkY+ty;
    int xidx = blkX+tx;

    // load data if it is within the valid input range
    int loadYidx=yidx, loadXidx=xidx;
    int index = m*loadYidx+loadXidx;

    if(IN_RANGE(loadYidx, 0, n-1) && IN_RANGE(loadXidx, 0, m-1)){
        btile[ty][tx] = b[index];  // Load the temperature data from global memory to shared memory
    }
    __syncthreads();

    if((threadIdx.x>0 && threadIdx.x<(blockDim.x-1)) && 
       (threadIdx.y>0 && threadIdx.y<(blockDim.y-1)) &&
       (xidx>0 && xidx<(m-1)) &&
       (yidx>0 && yidx<(n-1))){
        //a [i * m + j] = w0 * b [i * m + j] + \
            w1 * (b [(i - 1) * m + j] + b [(i + 1) * m + j] + b [i * m + j - 1] + b [i * m + j + 1]) + \
            w2 * (b [(i - 1) * m + j - 1] + b [(i - 1) * m + j + 1] + b [(i + 1) * m + j - 1] + b [(i + 1) * m + j + 1])
        a [yidx * m + xidx] = w0 * btile[ty][tx] +
            w1 * (btile[ty-1][tx] + btile[ty+1][tx] + btile[ty][tx-1] + btile[ty][tx+1]) +
            w2 * (btile[ty-1][tx-1] + btile[ty-1][tx+1] + btile[ty+1][tx-1] + btile[ty+1][tx+1]);
    }
}

