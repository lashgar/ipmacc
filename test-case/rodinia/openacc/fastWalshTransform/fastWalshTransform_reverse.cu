/*
 * Copyright 1993-2010 NVIDIA Corporation.  All rights reserved.
 *
 * Please refer to the NVIDIA end user license agreement (EULA) associated
 * with this source code for terms and conditions that govern your use of
 * this software. Any use, reproduction, disclosure, or distribution of
 * this software and related documentation outside the terms of the EULA
 * is strictly prohibited.
 *
 */



#ifndef FWT_KERNEL_CUH
#define FWT_KERNEL_CUH
#ifndef fwt_kernel_cuh
#define fwt_kernel_cuh



///////////////////////////////////////////////////////////////////////////////
// Elementary(for vectors less than elementary size) in-shared memory 
// combined radix-2 + radix-4 Fast Walsh Transform 
///////////////////////////////////////////////////////////////////////////////
#define ELEMENTARY_LOG2SIZE 11

void fwtBatch1Kernel(float *d_Output, float *d_Input, int log2N, int DIMX){
    for(tidx=0; tidx<DIMX; tidx++){
        const int    N = 1 << log2N;
        const int base = (tidx/BLOCKDIMX)<<log2N; //blockIdx.x << log2N;

        //(2 ** 11) * 4 bytes == 8KB -- maximum s_data[] size for G80
        float s_data[N];
        float *d_Src = d_Input  + base;
        float *d_Dst = d_Output + base;

        for(int pos = threadIdx.x; pos < N; pos += blockDim.x)
            s_data[pos] = d_Input[base+pos];//d_Src[pos];

        //Main radix-4 stages
        const int pos = tidx%BLOCKDIMY;//threadIdx.x;
        for(int stride = base + (N >> 2); stride > (base+0); stride >>= 2){
            int lo =        (pos & (stride - 1));
            int i0 = base + (((pos - lo) << 2) + lo);
            int i1 = base + (i0 + stride);
            int i2 = base + (i1 + stride);
            int i3 = base + (i2 + stride);

            __syncthreads();
            float D0 = d_Input[i0];//s_data[i0];
            float D1 = d_Input[i1];//s_data[i1];
            float D2 = d_Input[i2];//s_data[i2];
            float D3 = d_Input[i3];//s_data[i3];

            float T;
            T = D0; D0         = D0 + D2; D2         = T - D2;
            T = D1; D1         = D1 + D3; D3         = T - D3;
            T = D0; d_Input[i0]/*s_data[i0]*/ = D0 + D1; d_Input[i1]/*s_data[i1]*/ = T - D1;
            T = D2; d_Input[i2]/*s_data[i2]*/ = D2 + D3; d_Input[i3]/*s_data[i3]*/ = T - D3;
        }

        //Do single radix-2 stage for odd power of two
        if(log2N & 1){
            __syncthreads();
            for(int pos = threadIdx.x; pos < N / 2; pos += blockDim.x){
                int i0 = pos << 1;
                int i1 = i0 + 1;

                float D0 = s_data[i0];
                float D1 = s_data[i1];
                s_data[i0] = D0 + D1;
                s_data[i1] = D0 - D1;
            }
        }

        __syncthreads();
        for(int pos = threadIdx.x; pos < N; pos += blockDim.x)
            d_Dst[pos] = s_data[pos];
    }
}

////////////////////////////////////////////////////////////////////////////////
// Single in-global memory radix-4 Fast Walsh Transform pass
// (for strides exceeding elementary vector size)
////////////////////////////////////////////////////////////////////////////////
void fwtBatch2Kernel(
    float *d_Output,
    float *d_Input,
    int stride,
    int DIMX,
    int DIMY
){
    //#define DIMX (blockDim.x*gridDim.x)
    //#define DIMY (blockDim.y*gridDim.y)
    //#define BLOCKDIMY 16 
    for(tidy=0; tidy<DIMY; tidy++){
        for(tidx=0; tidx<DIMX; tidx++){
            const int pos = tidx; // blockIdx.x * blockDim.x + threadIdx.x;
            const int   N = DIMX*4;//blockDim.x *  gridDim.x * 4;

            //float *d_Src = d_Input + blockIdx.y * N;
            //float *d_Dst = d_Output + blockIdx.y * N;
            float offset = tidy*N;

            int lo = pos & (stride - 1);
            int i0 = ((pos - lo) << 2) + lo;
            int i1 = i0 + stride;
            int i2 = i1 + stride;
            int i3 = i2 + stride;

            float D0 = d_Input[offset+i0];
            float D1 = d_Input[offset+i1];
            float D2 = d_Input[offset+i2];
            float D3 = d_Input[offset+i3];

            float T;
            T = D0; D0        = D0 + D2;           D2 = T - D2;
            T = D1; D1        = D1 + D3;           D3 = T - D3;
            T = D0; d_Output[offset+i0] = D0 + D1; d_Output[offset+i1] = T - D1;
            T = D2; d_Output[offset+i2] = D2 + D3; d_Output[offset+i3] = T - D3;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// Put everything together: batched Fast Walsh Transform CPU front-end
////////////////////////////////////////////////////////////////////////////////
void fwtBatchGPU(float *d_Data, int M, int log2N){
    const int THREAD_N = 256;

    int N = 1 << log2N;
    //dim3 grid((1 << log2N) / (4 * THREAD_N), M, 1);
    for(; log2N > ELEMENTARY_LOG2SIZE; log2N -= 2, N >>= 2, M <<= 2){
        //fwtBatch2Kernel<<<grid, THREAD_N>>>(d_Data,
        fwtBatch2Kernel(d_Data,
            d_Data,
            N / 4,
            (1 << log2N) / (4 * THREAD_N),
            M);
        //cutilCheckMsg("fwtBatch2Kernel() execution failed\n");
    }

    fwtBatch1Kernel<<<M, N / 4, N * sizeof(float)>>>(
        d_Data,
        d_Data,
        log2N
    );
    cutilCheckMsg("fwtBatch1Kernel() execution failed\n");
}



////////////////////////////////////////////////////////////////////////////////
// Modulate two arrays
////////////////////////////////////////////////////////////////////////////////
__global__ void modulateKernel(float *d_A, float *d_B, int N){
    int        tid = blockIdx.x * blockDim.x + threadIdx.x;
    int numThreads = blockDim.x * gridDim.x;
    float     rcpN = 1.0f / (float)N;

    for(int pos = tid; pos < N; pos += numThreads)
        d_A[pos] *= d_B[pos] * rcpN;
}

//Interface to modulateKernel()
void modulateGPU(float *d_A, float *d_B, int N){
    modulateKernel<<<128, 256>>>(d_A, d_B, N);
}



#endif
#endif
