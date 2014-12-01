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

#define SHARED_SIZE_LIMIT 1024U
#define     SAMPLE_STRIDE 128




#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
//#include <cutil_inline.h>
//#include <shrQATest.h>
//#include "mergeSort_common.h"



////////////////////////////////////////////////////////////////////////////////
// Validate sorted keys array (check for integrity and proper order)
////////////////////////////////////////////////////////////////////////////////
uint validateSortedKeys(
        uint *resKey,
        uint *srcKey,
        uint batchSize,
        uint arrayLength,
        uint numValues,
        uint sortDir
        ){
    uint *srcHist;
    uint *resHist;
    if(arrayLength < 2){
        printf("validateSortedKeys(): arrays too short, exiting...\n");
        return 1;
    }

    printf("...inspecting keys array: ");
    srcHist = (uint *)malloc(numValues * sizeof(uint));
    resHist = (uint *)malloc(numValues * sizeof(uint));

    int flag = 1;
    for(uint j = 0; j < batchSize; j++, srcKey += arrayLength, resKey += arrayLength){
        //Build histograms for keys arrays
        memset(srcHist, 0, numValues * sizeof(uint));
        memset(resHist, 0, numValues * sizeof(uint));
        for(uint i = 0; i < arrayLength; i++){
            if( (srcKey[i] < numValues) && (resKey[i] < numValues) ){
                srcHist[srcKey[i]]++;
                resHist[resKey[i]]++;
            }else{
                fprintf(stderr, "***Set %u source/result key arrays are not limited properly***\n", j);
                flag = 0;
                goto brk;
            }
        }

        //Compare the histograms
        for(uint i = 0; i < numValues; i++)
            if(srcHist[i] != resHist[i]){
                fprintf(stderr, "***Set %u source/result keys histograms do not match***\n", j);
                flag = 0;
                goto brk;
            }
        //Finally check the ordering
        for(uint i = 0; i < arrayLength - 1; i++)
            if( (sortDir && (resKey[i] > resKey[i + 1])) || (!sortDir && (resKey[i] < resKey[i + 1])) ){
                fprintf(stderr, "***Set %u result key array is not ordered properly***\n", j);
                flag = 0;
                goto brk;
            }
    }

brk:
    free(resHist);
    free(srcHist);

    if(flag) printf("OK\n");
    return flag;
}



////////////////////////////////////////////////////////////////////////////////
// Value validation / stability check routines
////////////////////////////////////////////////////////////////////////////////
void fillValues(
        uint *val,
        uint N
        ){
    for(uint i = 0; i < N; i++)
        val[i] = i;
}

int validateSortedValues(
        uint *resKey,
        uint *resVal,
        uint *srcKey,
        uint batchSize,
        uint arrayLength
        ){
    int correctFlag = 1, stableFlag = 1;

    printf("...inspecting keys and values array: ");
    for(uint i = 0; i < batchSize; i++, resKey += arrayLength, resVal += arrayLength){
        for(uint j = 0; j < arrayLength; j++){
            if(resKey[j] != srcKey[resVal[j]])
                correctFlag = 0;

            if( (j < arrayLength - 1) && (resKey[j] == resKey[j + 1]) && (resVal[j] > resVal[j + 1]) )
                stableFlag = 0;
        }
    }

    printf(correctFlag ? "OK\n" : "***corrupted!!!***\n");
    printf(stableFlag ? "...stability property: stable!\n" : "...stability property: NOT stable\n");

    return correctFlag;
}
////////////////////////////////////////////////////////////////////////////////
// Helper functions
////////////////////////////////////////////////////////////////////////////////
static void checkOrder(uint *data, uint N, uint sortDir){
    if(N <= 1)
        return;

    for(uint i = 0; i < N - 1; i++)
        if( (sortDir && (data[i] > data[i + 1])) || (!sortDir && (data[i] < data[i + 1])) ){
            fprintf(stderr, "checkOrder() failed!!!\n");
            exit(-1);
        }
}

static uint umin(uint a, uint b){
    return (a <= b) ? a : b;
}

static uint getSampleCount(uint dividend){
    return ( (dividend % SAMPLE_STRIDE) != 0 ) ? (dividend / SAMPLE_STRIDE + 1) : (dividend / SAMPLE_STRIDE);
}

static uint nextPowerOfTwo(uint x){
    --x;
    x |= x >> 1;
    x |= x >> 2;
    x |= x >> 4;
    x |= x >> 8;
    x |= x >> 16;
    return ++x;
}

static uint binarySearchInclusive(uint val, uint *data, uint L, uint sortDir){
    if(L == 0)
        return 0;

    uint pos = 0;
    for(uint stride = nextPowerOfTwo(L); stride > 0; stride >>= 1){
        uint newPos = umin(pos + stride, L);
        if( (sortDir && (data[newPos - 1] <= val)) || (!sortDir && (data[newPos - 1] >= val)) )
            pos = newPos;
    }

    return pos;
}

static uint binarySearchExclusive(uint val, uint *data, uint L, uint sortDir){
    if(L == 0)
        return 0;

    uint pos = 0;
    for(uint stride = nextPowerOfTwo(L); stride > 0; stride >>= 1){
        uint newPos = umin(pos + stride, L);
        if( (sortDir && (data[newPos - 1] < val)) || (!sortDir && (data[newPos - 1] > val)) )
            pos = newPos;
    }

    return pos;
}


////////////////////////////////////////////////////////////////////////////////
// Merge step 1: find sample ranks in each segment
////////////////////////////////////////////////////////////////////////////////
static void generateSampleRanks(
        uint *ranksA,
        uint *ranksB,
        uint *srcKey,
        uint stride,
        uint N,
        uint sortDir
        ){
    uint lastSegmentElements = N % (2 * stride);
    uint         sampleCount = (lastSegmentElements > stride) ? (N + 2 * stride - lastSegmentElements) / (2 * SAMPLE_STRIDE) : (N - lastSegmentElements) / (2 * SAMPLE_STRIDE);

    #pragma acc kernels copy(ranksA[0:getSampleCount(N)],ranksB[0:getSampleCount(N)],srcKey[0:getSampleCount(N)])
    #pragma acc loop independent 
    for(uint pos = 0; pos < sampleCount; pos++)
    {
        const uint           i = pos & ( (stride / SAMPLE_STRIDE) - 1 );
        const uint segmentBase = (pos - i) * (2 * SAMPLE_STRIDE);

        const uint lenA = stride;
        const uint lenB = umin(stride, N - segmentBase - stride);
        const uint   nA = stride / SAMPLE_STRIDE;
        const uint   nB = getSampleCount(lenB);
        uint posi = 0 ;
        if(i < nA){

            if(lenB == 0)
                posi = 0 ;
            uint val = srcKey[segmentBase + i * SAMPLE_STRIDE];
            uint *data =  srcKey + segmentBase + stride;
            uint pow = lenB ;    
            --pow;
            pow |= pow >> 1;
            pow |= pow >> 2;
            pow |= pow >> 4;
            pow |= pow >> 8;
            pow |= pow >> 16;
            pow++ ; 

            for(uint stride_itr = pow; stride_itr > 0; stride_itr >>= 1){
                uint newPos = (posi + stride_itr) <= lenB ? posi + stride_itr : lenB;
                if( (sortDir && (data[newPos - 1] < val)) || (!sortDir && (data[newPos - 1] > val)) )
                    posi = newPos;
            }

            ranksA[(segmentBase +      0) / SAMPLE_STRIDE + i] = i * SAMPLE_STRIDE;
            ranksB[(segmentBase +      0) / SAMPLE_STRIDE + i] = posi ;
            // binarySearchExclusive(srcKey[segmentBase + i * SAMPLE_STRIDE], srcKey + segmentBase + stride, lenB, sortDir);
        }
        posi = 0 ;
        if(i < nB){

            if(lenA == 0)
                posi = 0 ;
            uint val = srcKey[segmentBase + stride + i * SAMPLE_STRIDE];
            uint *data =  srcKey + segmentBase;

            uint pow = lenA ;    
            --pow;
            pow |= pow >> 1;
            pow |= pow >> 2;
            pow |= pow >> 4;
            pow |= pow >> 8;
            pow |= pow >> 16;
            pow++ ; 


            for(uint stride_itr = pow ; stride_itr > 0; stride_itr >>= 1){

                uint newPos = (posi + stride_itr) <= lenA ? posi + stride_itr : lenA;
                if( (sortDir && (data[newPos - 1] <= val)) || (!sortDir && (data[newPos - 1] >= val)) )
                    posi = newPos;
            }



            ranksB[(segmentBase + stride) / SAMPLE_STRIDE + i] = i * SAMPLE_STRIDE;
            ranksA[(segmentBase + stride) / SAMPLE_STRIDE + i] =posi ;
            // binarySearchInclusive(srcKey[segmentBase + stride + i * SAMPLE_STRIDE], srcKey + segmentBase, lenA, sortDir);
        }
    }
}

static void generateSampleRanks_parallel(
        uint *ranksA,
        uint *ranksB,
        uint *srcKey,
        uint stride,
        uint N,
        uint sortDir
        ){
    uint lastSegmentElements = N % (2 * stride);
    uint         sampleCount = (lastSegmentElements > stride) ? (N + 2 * stride - lastSegmentElements) / (2 * SAMPLE_STRIDE) : (N - lastSegmentElements) / (2 * SAMPLE_STRIDE);

    for(uint pos = 0; pos < sampleCount; pos++){
        const uint           i = pos & ( (stride / SAMPLE_STRIDE) - 1 );
        const uint segmentBase = (pos - i) * (2 * SAMPLE_STRIDE);

        const uint lenA = stride;
        const uint lenB = umin(stride, N - segmentBase - stride);
        const uint   nA = stride / SAMPLE_STRIDE;
        const uint   nB = getSampleCount(lenB);

        if(i < nA){
            ranksA[(segmentBase +      0) / SAMPLE_STRIDE + i] = i * SAMPLE_STRIDE;
            ranksB[(segmentBase +      0) / SAMPLE_STRIDE + i] = binarySearchExclusive(srcKey[segmentBase + i * SAMPLE_STRIDE], srcKey + segmentBase + stride, lenB, sortDir);
        }

        if(i < nB){
            ranksB[(segmentBase + stride) / SAMPLE_STRIDE + i] = i * SAMPLE_STRIDE;
            ranksA[(segmentBase + stride) / SAMPLE_STRIDE + i] = binarySearchInclusive(srcKey[segmentBase + stride + i * SAMPLE_STRIDE], srcKey + segmentBase, lenA, sortDir);
        }
    }
}



////////////////////////////////////////////////////////////////////////////////
// Merge step 2: merge ranks and indices to derive elementary intervals
////////////////////////////////////////////////////////////////////////////////
static void mergeRanksAndIndices(
        uint *limits,
        uint *ranks,
        uint stride,
        uint N
        ){
    uint lastSegmentElements = N % (2 * stride);
    uint         sampleCount = (lastSegmentElements > stride) ? (N + 2 * stride - lastSegmentElements) / (2 * SAMPLE_STRIDE) : (N - lastSegmentElements) / (2 * SAMPLE_STRIDE);

    for(uint pos = 0; pos < sampleCount; pos++){
        const uint           i = pos & ( (stride / SAMPLE_STRIDE) - 1 );
        const uint segmentBase = (pos - i) * (2 * SAMPLE_STRIDE);

        const uint lenA = stride;
        const uint lenB = umin(stride, N - segmentBase - stride);
        const uint   nA = stride / SAMPLE_STRIDE;
        const uint   nB = getSampleCount(lenB);

        if(i < nA){
            uint dstPosA = binarySearchExclusive(ranks[(segmentBase + 0) / SAMPLE_STRIDE + i], ranks + (segmentBase + stride) / SAMPLE_STRIDE, nB, 1) + i;
            assert( dstPosA < nA + nB );
            limits[(segmentBase / SAMPLE_STRIDE) + dstPosA] = ranks[(segmentBase + 0) / SAMPLE_STRIDE + i];
        }

        if(i < nB){
            uint dstPosA = binarySearchInclusive(ranks[(segmentBase + stride) / SAMPLE_STRIDE + i], ranks + (segmentBase + 0) / SAMPLE_STRIDE, nA, 1) + i;
            assert( dstPosA < nA + nB );
            limits[(segmentBase / SAMPLE_STRIDE) + dstPosA] = ranks[(segmentBase + stride) / SAMPLE_STRIDE + i];
        }
    }
}


////////////////////////////////////////////////////////////////////////////////
// Merge step 3: merge elementary intervals (each interval is <= SAMPLE_STRIDE)
////////////////////////////////////////////////////////////////////////////////
static void merge(
        uint *dstKey,
        uint *dstVal,
        uint *srcAKey,
        uint *srcAVal,
        uint *srcBKey,
        uint *srcBVal,
        uint lenA,
        uint lenB,
        uint sortDir
        ){
    checkOrder(srcAKey, lenA, sortDir);
    checkOrder(srcBKey, lenB, sortDir);

    for(uint i = 0; i < lenA; i++){
        uint dstPos = binarySearchExclusive(srcAKey[i], srcBKey, lenB, sortDir) + i;
        assert( dstPos < lenA + lenB );
        dstKey[dstPos] = srcAKey[i];
        dstVal[dstPos] = srcAVal[i];
    }

    for(uint i = 0; i < lenB; i++){
        uint dstPos = binarySearchInclusive(srcBKey[i], srcAKey, lenA, sortDir) + i;
        assert( dstPos < lenA + lenB );
        dstKey[dstPos] = srcBKey[i];
        dstVal[dstPos] = srcBVal[i];
    }
}

static void mergeElementaryIntervals(
        uint *dstKey,
        uint *dstVal,
        uint *srcKey,
        uint *srcVal,
        uint *limitsA,
        uint *limitsB,
        uint stride,
        uint N,
        uint sortDir
        ){
    uint lastSegmentElements = N % (2 * stride);
    uint          mergePairs = (lastSegmentElements > stride) ? getSampleCount(N) : (N - lastSegmentElements) / SAMPLE_STRIDE;

    for(uint pos = 0; pos < mergePairs; pos++){
        uint           i = pos & ( (2 * stride) / SAMPLE_STRIDE - 1 );
        uint segmentBase = (pos - i) * SAMPLE_STRIDE;

        const uint lenA = stride;
        const uint lenB = umin(stride, N - segmentBase - stride);
        const uint   nA = stride / SAMPLE_STRIDE;
        const uint   nB = getSampleCount(lenB);
        const uint    n = nA + nB;

        const uint   startPosA = limitsA[pos];
        const uint     endPosA = (i + 1 < n) ? limitsA[pos + 1] : lenA;
        const uint   startPosB = limitsB[pos];
        const uint     endPosB = (i + 1 < n) ? limitsB[pos + 1] : lenB;
        const uint startPosDst = startPosA + startPosB;

        assert( startPosA <= endPosA && endPosA <= lenA);
        assert( startPosB <= endPosB && endPosB <= lenB);
        assert( (endPosA - startPosA) <= SAMPLE_STRIDE);
        assert( (endPosB - startPosB) <= SAMPLE_STRIDE);

        merge(
                dstKey  + segmentBase + startPosDst,
                dstVal  + segmentBase + startPosDst,
                (srcKey + segmentBase +      0) + startPosA,
                (srcVal + segmentBase +      0) + startPosA,
                (srcKey + segmentBase + stride) + startPosB,
                (srcVal + segmentBase + stride) + startPosB,
                endPosA - startPosA,
                endPosB - startPosB,
                sortDir
             );
    }
}





////////////////////////////////////////////////////////////////////////////////
// Retarded bubble sort
////////////////////////////////////////////////////////////////////////////////
static void bubbleSort(uint *key, uint *val, uint N, uint sortDir){
    if(N <= 1)
        return;

    for(uint bottom = 0; bottom < N - 1; bottom++){
        uint savePos = bottom;
        uint saveKey = key[bottom];

        for(uint i = bottom + 1; i < N; i++)
            if(
                    (sortDir && (key[i] < saveKey)) ||
                    (!sortDir && (key[i] > saveKey))
              ){
                savePos = i;
                saveKey = key[i];
            }

        if(savePos != bottom){
            uint t;
            t = key[savePos]; key[savePos] = key[bottom]; key[bottom] = t;
            t = val[savePos]; val[savePos] = val[bottom]; val[bottom] = t;
        }
    }
}





////////////////////////////////////////////////////////////////////////////////
// Interface function
////////////////////////////////////////////////////////////////////////////////
void mergeSortHost(
        uint *dstKey,
        uint *dstVal,
        uint *bufKey,
        uint *bufVal,
        uint *srcKey,
        uint *srcVal,
        uint N,
        uint sortDir
        ){
    uint *ikey, *ival, *okey, *oval;
    uint stageCount = 0;
    for(uint stride = SHARED_SIZE_LIMIT; stride < N; stride <<= 1, stageCount++);
    if(stageCount & 1){
        ikey = bufKey;
        ival = bufVal;
        okey = dstKey;
        oval = dstVal;
    }else{
        ikey = dstKey;
        ival = dstVal;
        okey = bufKey;
        oval = bufVal;
    }

    printf("Bottom-level sort...\n");
    memcpy(ikey, srcKey, N * sizeof(uint));
    memcpy(ival, srcVal, N * sizeof(uint));
    for(uint pos = 0; pos < N; pos += SHARED_SIZE_LIMIT)
        bubbleSort(ikey + pos, ival + pos, umin(SHARED_SIZE_LIMIT, N - pos), sortDir);

    printf("Merge...\n");
    uint  *ranksA = (uint *)malloc( getSampleCount(N) * sizeof(uint) );
    uint  *ranksB = (uint *)malloc( getSampleCount(N) * sizeof(uint) );
    uint *limitsA = (uint *)malloc( getSampleCount(N) * sizeof(uint) );
    uint *limitsB = (uint *)malloc( getSampleCount(N) * sizeof(uint) );
    memset(ranksA,  0xFF, getSampleCount(N) * sizeof(uint));
    memset(ranksB,  0xFF, getSampleCount(N) * sizeof(uint));
    memset(limitsA, 0xFF, getSampleCount(N) * sizeof(uint));
    memset(limitsB, 0xFF, getSampleCount(N) * sizeof(uint));

    for(uint stride = SHARED_SIZE_LIMIT; stride < N; stride <<= 1){
        uint lastSegmentElements = N % (2 * stride);

        //Find sample ranks and prepare for limiters merge
        generateSampleRanks(ranksA, ranksB, ikey, stride, N, sortDir);

        //Merge ranks and indices
        mergeRanksAndIndices(limitsA, ranksA, stride, N);
        mergeRanksAndIndices(limitsB, ranksB, stride, N);

        //Merge elementary intervals
        mergeElementaryIntervals(okey, oval, ikey, ival, limitsA, limitsB, stride, N, sortDir);

        if( lastSegmentElements <= stride ) {
            //Last merge segment consists of a single array which just needs to be passed through
            memcpy(okey + (N - lastSegmentElements), ikey + (N - lastSegmentElements), lastSegmentElements * sizeof(uint));
            memcpy(oval + (N - lastSegmentElements), ival + (N - lastSegmentElements), lastSegmentElements * sizeof(uint));
        }

        uint *t;
        t = ikey; ikey = okey; okey = t;
        t = ival; ival = oval; oval = t;
    }
    printf("End of Merge...\n");
    printf("End of Merge...\n");


    free(limitsB);
    free(limitsA);
    free(ranksB);
    free(ranksA);
}

////////////////////////////////////////////////////////////////////////////////
// Test driver
////////////////////////////////////////////////////////////////////////////////
int main(int argc, char** argv){
    uint *h_SrcKey, *h_SrcVal, *h_DstKey, *h_DstVal;
    uint *d_SrcKey, *d_SrcVal, *d_BufKey, *d_BufVal, *d_DstKey, *d_DstVal;
    uint *h_BufVal, *h_BufKey;
    uint hTimer;

    const uint   N = 4 * 1048576;
    const uint DIR = 1;
    const uint numValues = 65536;

    //	shrQAStart(argc, argv);

    printf("Allocating and initializing host arrays...\n\n");
    //     cutCreateTimer(&hTimer);
    h_SrcKey = (uint *)malloc(N * sizeof(uint));
    h_SrcVal = (uint *)malloc(N * sizeof(uint));
    h_DstKey = (uint *)malloc(N * sizeof(uint));
    h_DstVal = (uint *)malloc(N * sizeof(uint));
    h_BufVal = (uint *)malloc(N * sizeof(uint));
    h_BufKey = (uint *)malloc(N * sizeof(uint));

    srand(2009);
    for(uint i = 0; i < N; i++)
        h_SrcKey[i] = rand() % numValues;
    fillValues(h_SrcVal, N);

    /*    printf("Allocating and initializing CUDA arrays...\n\n");
          cutilSafeCall( cudaMalloc((void **)&d_DstKey, N * sizeof(uint)) );
          cutilSafeCall( cudaMalloc((void **)&d_DstVal, N * sizeof(uint)) );
          cutilSafeCall( cudaMalloc((void **)&d_BufKey, N * sizeof(uint)) );
          cutilSafeCall( cudaMalloc((void **)&d_BufVal, N * sizeof(uint)) );
          cutilSafeCall( cudaMalloc((void **)&d_SrcKey, N * sizeof(uint)) );
          cutilSafeCall( cudaMalloc((void **)&d_SrcVal, N * sizeof(uint)) );
          cutilSafeCall( cudaMemcpy(d_SrcKey, h_SrcKey, N * sizeof(uint), cudaMemcpyHostToDevice) );
          cutilSafeCall( cudaMemcpy(d_SrcVal, h_SrcVal, N * sizeof(uint), cudaMemcpyHostToDevice) );

          printf("Initializing GPU merge sort...\n");
          initMergeSort();

          printf("Running GPU merge sort...\n");
          cutilSafeCall( cutilDeviceSynchronize() );
          cutResetTimer(hTimer);
          cutStartTimer(hTimer);
          mergeSort(
          d_DstKey,
          d_DstVal,
          d_BufKey,
          d_BufVal,
          d_SrcKey,
          d_SrcVal,
          N,
          DIR
          );
          cutilSafeCall( cutilDeviceSynchronize() );
          cutStopTimer(hTimer);
          printf("Time: %f ms\n", cutGetTimerValue(hTimer));

          printf("Reading back GPU merge sort results...\n");
          cutilSafeCall( cudaMemcpy(h_DstKey, d_DstKey, N * sizeof(uint), cudaMemcpyDeviceToHost) );
          cutilSafeCall( cudaMemcpy(h_DstVal, d_DstVal, N * sizeof(uint), cudaMemcpyDeviceToHost) );
          */

    double tic = clock();
    printf("Running CPU merge sort...\n");
    mergeSortHost(
            h_DstKey,
            h_DstVal,
            h_BufKey,
            h_BufVal,
            h_SrcKey,
            h_SrcVal,
            N,
            DIR
            );
    double toc = clock();
    printf("Time: %f ms\n", toc - tic );

    printf("Inspecting the results...\n");
    uint keysFlag = validateSortedKeys(
            h_DstKey,
            h_SrcKey,
            1,
            N,
            numValues,
            DIR
            );

    uint valuesFlag = validateSortedValues(
            h_DstKey,
            h_DstVal,
            h_SrcKey,
            1,
            N
            );

    printf("Shutting down...\n");
    free(h_DstVal);
    free(h_DstKey);
    free(h_SrcVal);
    free(h_SrcKey);
    //       cutilDeviceReset();

    //        shrQAFinishExit(argc, (const char **)argv, (keysFlag && valuesFlag) ? QA_PASSED : QA_FAILED);
}
