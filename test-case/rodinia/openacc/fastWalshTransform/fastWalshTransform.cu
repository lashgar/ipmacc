/*
 * Copyright 1993-2014 NVIDIA Corporation.  All rights reserved.
 *
 * Please refer to the NVIDIA end user license agreement (EULA) associated
 * with this source code for terms and conditions that govern your use of
 * this software. Any use, reproduction, disclosure, or distribution of
 * this software and related documentation outside the terms of the EULA
 * is strictly prohibited.
 *
 */

/*
 * Walsh transforms belong to a class of generalized Fourier transformations.
 * They have applications in various fields of electrical engineering
 * and numeric theory. In this sample we demonstrate efficient implementation
 * of naturally-ordered Walsh transform
 * (also known as Walsh-Hadamard or Hadamard transform) in CUDA and its
 * particular application to dyadic convolution computation.
 * Refer to excellent Jorg Arndt's "Algorithms for Programmers" textbook
 * http://www.jjj.de/fxt/fxtbook.pdf (Chapter 22)
 *
 * Victor Podlozhnyuk (vpodlozhnyuk@nvidia.com)
 */



#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <helper_functions.h>
#include <helper_cuda.h>
#include "openacc.h"


////////////////////////////////////////////////////////////////////////////////
// Reference CPU FWT
////////////////////////////////////////////////////////////////////////////////
extern"C" void fwtCPU(float *h_Output, float *h_Input, int log2N);
extern"C" void slowWTcpu(float *h_Output, float *h_Input, int log2N);
extern "C" void dyadicConvolutionCPU(
        float *h_Result,
        float *h_Data,
        float *h_Kernel,
        int log2dataN,
        int log2kernelN
        );
extern void fwtCPU_openacc(float *h_Output, float *h_Input, int log2N);
extern void dyadicConvolutionCPU_openacc(
        float *h_Result_f,
        float *h_Data_f,
        float *h_Kernel_f,
        int log2dataN,
        int log2kernelN);


////////////////////////////////////////////////////////////////////////////////
// GPU FWT
////////////////////////////////////////////////////////////////////////////////
#include "fastWalshTransform_kernel.cuh"



////////////////////////////////////////////////////////////////////////////////
// Data configuration
////////////////////////////////////////////////////////////////////////////////
int log2Kernel = 7;
  int log2Data = 23;

int   dataN = 1 << log2Data;
int kernelN = 1 << log2Kernel;

int   DATA_SIZE = dataN   * sizeof(float);
int KERNEL_SIZE = kernelN * sizeof(float);

double NOPS = 3.0 * (double)dataN * (double)log2Data / 2.0;



////////////////////////////////////////////////////////////////////////////////
// Main program
////////////////////////////////////////////////////////////////////////////////
int main(int argc, char *argv[])
{
    #ifdef __NVCUDA__
    	acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    	acc_init( acc_device_nvocl );
    	//acc_list_devices_spec( acc_device_nvocl );
    #endif 

    if (checkCmdLineFlag(argc, (const char **) argv, "log2Data"))
    {
        log2Data = getCmdLineArgumentInt(argc, (const char **)argv, "log2Data");
        dataN = 1 << log2Data;
        DATA_SIZE = dataN   * sizeof(float);
        NOPS = 3.0 * (double)dataN * (double)log2Data / 2.0;
    }

    float *h_Data,
          *h_Kernel,
          *h_ResultCPU,
          *h_ResultGPU;

    float *d_Data,
          *d_Kernel;

    double delta, ref, sum_delta2, sum_ref2, L2norm, gpuTime;

    StopWatchInterface *hTimer = NULL;
    int i;

    printf("%s Starting...\n\n", argv[0]);

    // use command-line specified CUDA device, otherwise use device with highest Gflops/s
    findCudaDevice(argc, (const char **)argv);

    sdkCreateTimer(&hTimer);

    printf("Initializing data...\n");
    printf("...allocating CPU memory\n");
    h_Kernel    = (float *)malloc(KERNEL_SIZE);
    h_Data      = (float *)malloc(DATA_SIZE);
    h_ResultCPU = (float *)malloc(DATA_SIZE);
    h_ResultGPU = (float *)malloc(DATA_SIZE);

    printf("...generating data\n");
    printf("Data length: %i; kernel length: %i\n", dataN, kernelN);
    srand(2007);

    for (i = 0; i < kernelN; i++)
    {
        h_Kernel[i] = (float)rand() / (float)RAND_MAX;
    }

    for (i = 0; i < dataN; i++)
    {
        h_Data[i] = (float)rand() / (float)RAND_MAX;
    }

    bool run_cuda=false;
    bool run_openacc=false;
    run_cuda     = (checkCmdLineFlag(argc, (const char **) argv, "cuda") != 0);
    run_openacc  = (checkCmdLineFlag(argc, (const char **) argv, "openacc") != 0);
    if(!(run_cuda || run_openacc)){
        printf("exiting without running either cuda or openacc\n");
        exit(-1);
    }

    //#define RUNFWHONLY 1
    //if(RUNFWHONLY){
    //    if(run_cuda){
    //        printf("...allocating GPU memory\n");
    //        checkCudaErrors(cudaMalloc((void **)&d_Data,   DATA_SIZE));
    //        checkCudaErrors(cudaMemcpy(d_Data,   h_Data,     DATA_SIZE, cudaMemcpyHostToDevice));

    //        printf("Running GPU FastWalschTransformation...\n");
    //        checkCudaErrors(cudaDeviceSynchronize());
    //        sdkResetTimer(&hTimer);
    //        sdkStartTimer(&hTimer);
    //        fwtBatchGPU(d_Data, 1, log2Data);
    //        checkCudaErrors(cudaDeviceSynchronize());
    //        sdkStopTimer(&hTimer);
    //        gpuTime = sdkGetTimerValue(&hTimer);
    //        printf("GPU time: %f ms; GOP/s: %f\n", gpuTime, NOPS / (gpuTime * 0.001 * 1E+9));
    //        printf("Reading back GPU results...\n");
    //        checkCudaErrors(cudaMemcpy(h_ResultGPU, d_Data, DATA_SIZE, cudaMemcpyDeviceToHost));
    //    }

    //    if(run_openacc){
    //        //printf("Running straightforward CPU dyadic convolution...\n");
    //        //dyadicConvolutionCPU(h_ResultCPU, h_Data, h_Kernel, log2Data, log2Kernel);
    //        printf("Running OpenACC fastWalshTransform...\n");
    //        fwtCPU_openacc(h_ResultCPU, h_Data, log2Data);
    //    }
    //}else{
        if(run_cuda){
            printf("...allocating GPU memory\n");
            checkCudaErrors(cudaMalloc((void **)&d_Kernel, DATA_SIZE));
            checkCudaErrors(cudaMalloc((void **)&d_Data,   DATA_SIZE));
            checkCudaErrors(cudaMemset(d_Kernel, 0, DATA_SIZE));
            checkCudaErrors(cudaMemcpy(d_Kernel, h_Kernel, KERNEL_SIZE, cudaMemcpyHostToDevice));
            checkCudaErrors(cudaMemcpy(d_Data,   h_Data,     DATA_SIZE, cudaMemcpyHostToDevice));

            printf("Running CUDA dyadic convolution using Fast Walsh Transform...\n");
            checkCudaErrors(cudaDeviceSynchronize());
            sdkResetTimer(&hTimer);
            sdkStartTimer(&hTimer);
            fwtBatchGPU(d_Data, 1, log2Data);
            fwtBatchGPU(d_Kernel, 1, log2Data);
            modulateGPU(d_Data, d_Kernel, dataN);
            fwtBatchGPU(d_Data, 1, log2Data);
            checkCudaErrors(cudaDeviceSynchronize());
            sdkStopTimer(&hTimer);
            gpuTime = sdkGetTimerValue(&hTimer);
            printf("GPU time: %f ms; GOP/s: %f\n", gpuTime, NOPS / (gpuTime * 0.001 * 1E+9));
            printf("Reading back GPU results...\n");
            checkCudaErrors(cudaMemcpy(h_ResultGPU, d_Data, DATA_SIZE, cudaMemcpyDeviceToHost));
        }

        if(run_openacc){
            //printf("Running straightforward CPU dyadic convolution...\n");
            //dyadicConvolutionCPU(h_ResultCPU, h_Data, h_Kernel, log2Data, log2Kernel);
            printf("Running straightforward OpenACC dyadic convolution...\n");
            dyadicConvolutionCPU_openacc(h_ResultCPU, h_Data, h_Kernel, log2Data, log2Kernel);
        }

    //}

    if(run_openacc && run_cuda){
        printf("Comparing the results...\n");
        sum_delta2 = 0;
        sum_ref2   = 0;

        for (i = 0; i < dataN; i++)
        {
            delta       = h_ResultCPU[i] - h_ResultGPU[i];
            ref         = h_ResultCPU[i];
            sum_delta2 += delta * delta;
            sum_ref2   += ref * ref;
        }

        L2norm = sqrt(sum_delta2 / sum_ref2);
    }

    printf("Shutting down...\n");
    sdkDeleteTimer(&hTimer);
    if(run_cuda){
        checkCudaErrors(cudaFree(d_Data));
        /*if(!RUNFWHONLY)*/ checkCudaErrors(cudaFree(d_Kernel));
    }
    free(h_ResultGPU);
    free(h_ResultCPU);
    free(h_Data);
    free(h_Kernel);

    // cudaDeviceReset causes the driver to clean up all state. While
    // not mandatory in normal operation, it is good practice.  It is also
    // needed to ensure correct operation when the application is being
    // profiled. Calling cudaDeviceReset causes all profile data to be
    // flushed before the application exits
    cudaDeviceReset();
    printf("L2 norm: %E\n", L2norm);
    printf(L2norm < 1e-6 ? "Test passed\n" : "Test failed!\n");

    if(L2norm < 1e-6)
        return 0;
    else
        return -1;
}
