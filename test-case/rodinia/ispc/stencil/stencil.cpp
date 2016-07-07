/*
  Copyright (c) 2010-2014, Intel Corporation
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

    * Neither the name of Intel Corporation nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.


   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
   IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
   TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
   PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
   OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
   PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
   LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
   NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  
*/

#ifdef _MSC_VER
#define _CRT_SECURE_NO_WARNINGS
#define NOMINMAX
#pragma warning (disable: 4244)
#pragma warning (disable: 4305)
#endif

#include <cstdlib>
#include <stdio.h>
#include <algorithm>
#include <string.h>
#include <math.h>
#include "../timing.h"
#include "stencil_ispc.h"
#ifdef __NVOPENCL__
#include "openacc.h"
#endif

using namespace ispc;


extern void loop_stencil_serial(int t0, int t1, int x0, int x1,
                                int y0, int y1, int z0, int z1,
                                int Nx, int Ny, int Nz,
                                const float coef[5], 
                                const float vsq[],
                                float Aeven[], float Aodd[]);
extern void loop_stencil_openacc_multi(int t0, int t1, int x0, int x1,
                                int y0, int y1, int z0, int z1,
                                int Nx, int Ny, int Nz,
                                const float coef[5], 
                                const float vsq[],
                                float Aeven[], float Aodd[]);
extern void loop_stencil_openacc_single(int t0, int t1, int x0, int x1,
                                int y0, int y1, int z0, int z1,
                                int Nx, int Ny, int Nz,
                                const float coef[5], 
                                const float vsq[],
                                float Aeven[], float Aodd[]);


void InitData(int Nx, int Ny, int Nz, float *A[2], float *vsq) {
    int offset = 0;
    for (int z = 0; z < Nz; ++z)
        for (int y = 0; y < Ny; ++y)
            for (int x = 0; x < Nx; ++x, ++offset) {
                A[0][offset] = (x < Nx / 2) ? x / float(Nx) : y / float(Ny);
                A[1][offset] = 0;
                vsq[offset] = x*y*z / float(Nx * Ny * Nz);
            }
}


int main(int argc, char *argv[]) {
    static unsigned int test_iterations[] = {9, 9, 9};//the last two numbers must be equal here
    int Nx = 256, Ny = 256, Nz = 256;
    int width = 4;

    if (argc > 1) {
        if (strncmp(argv[1], "--scale=", 8) == 0) {
            float scale = atof(argv[1] + 8);
            Nx *= scale;
            Ny *= scale;
            Nz *= scale;
        }
    }
    if ((argc == 4) || (argc == 5)) {
        for (int i = 0; i < 3; i++) {
            test_iterations[i] = atoi(argv[argc - 3 + i]);
        }
    }

    #ifdef __NVOPENCL__
    printf("compiled for ocl\n");
    acc_init( acc_device_nvocl );
    #endif 

    float *Aserial[2], *Aispc[2], *Aopenacc[2];
    Aserial[0] = new float [Nx * Ny * Nz];
    Aserial[1] = new float [Nx * Ny * Nz];
    Aispc[0] = new float [Nx * Ny * Nz];
    Aispc[1] = new float [Nx * Ny * Nz];
    Aopenacc[0] = new float [Nx * Ny * Nz];
    Aopenacc[1] = new float [Nx * Ny * Nz];
    float *vsq = new float [Nx * Ny * Nz];

    float coeff[4] = { 0.5, -.25, .125, -.0625 }; 

    //
    // Compute the image using the ispc implementation on one core; report
    // the minimum time of three runs.
    //
    /*
    InitData(Nx, Ny, Nz, Aispc, vsq);
    double minTimeISPC = 1e30;
    for (unsigned int i = 0; i < test_iterations[0]; ++i) {
        reset_and_start_timer();
        loop_stencil_ispc(0, 7, width, Nx - width, width, Ny - width,
                          width, Nz - width, Nx, Ny, Nz, coeff, vsq,
                          Aispc[0], Aispc[1]);
        double dt = get_elapsed_msec();
        printf("@time of ISPC run:\t\t\t%.3f msec\n", dt);
        minTimeISPC = std::min(minTimeISPC, dt);
    }

    printf("[stencil ispc 1 core]:\t\t%.3f msec\n", minTimeISPC);
    */


    //
    // Compute the image using the ispc implementation with tasks; report
    // the minimum time of three runs.
    //
    InitData(Nx, Ny, Nz, Aispc, vsq);
    double minTimeISPCTasks = 1e30;
    for (unsigned int i = 0; i < test_iterations[1]; ++i) {
        reset_and_start_timer();
        loop_stencil_ispc_tasks(0, 7, width, Nx - width, width, Ny - width,
                                width, Nz - width, Nx, Ny, Nz, coeff, vsq,
                                Aispc[0], Aispc[1]);
        double dt = get_elapsed_msec();
        printf("@time of ISPC+TASKS run:\t\t\t%.3f msec\n", dt);
        minTimeISPCTasks = std::min(minTimeISPCTasks, dt);
    }

    printf("[stencil ispc + tasks]:\t\t%.3f msec\n", minTimeISPCTasks);

    /*
    // 
    // And run the serial implementation 3 times, again reporting the
    // minimum time.
    //
    InitData(Nx, Ny, Nz, Aserial, vsq);
    double minTimeSerial = 1e30;
    for (unsigned int i = 0; i < test_iterations[2]; ++i) {
        reset_and_start_timer();
        loop_stencil_serial(0, 7, width, Nx-width, width, Ny - width,
                            width, Nz - width, Nx, Ny, Nz, coeff, vsq,
                            Aserial[0], Aserial[1]);
        double dt = get_elapsed_msec();
        printf("@time of serial run:\t\t\t%.3f msec\n", dt);
        minTimeSerial = std::min(minTimeSerial, dt);
    }

    printf("[stencil serial]:\t\t%.3f msec\n", minTimeSerial);
    */

    // 
    // And run the serial implementation 3 times, again reporting the
    // minimum time.
    //
    /*
    InitData(Nx, Ny, Nz, Aopenacc, vsq);
    double minTimeOpenaccS = 1e30;
    for (unsigned int i = 0; i < test_iterations[2]; ++i) {
        reset_and_start_timer();
        loop_stencil_openacc_single(0, 7, width, Nx-width, width, Ny - width,
                            width, Nz - width, Nx, Ny, Nz, coeff, vsq,
                            Aopenacc[0], Aopenacc[1]);
        double dt = get_elapsed_msec();
        printf("@time of openacc-s run:\t\t\t%.3f msec\n", dt);
        minTimeOpenaccS = std::min(minTimeOpenaccS, dt);
    }

    printf("[stencil openacc-s]:\t\t%.3f msec\n", minTimeOpenaccS);
    */


    // 
    // And run the serial implementation 3 times, again reporting the
    // minimum time.
    //
    InitData(Nx, Ny, Nz, Aopenacc, vsq);
    double minTimeOpenacc = 1e30;
    for (unsigned int i = 0; i < test_iterations[2]; ++i) {
        reset_and_start_timer();
        loop_stencil_openacc_multi(0, 7, width, Nx-width, width, Ny - width,
                            width, Nz - width, Nx, Ny, Nz, coeff, vsq,
                            Aopenacc[0], Aopenacc[1]);
        double dt = get_elapsed_msec();
        printf("@time of openacc-m run:\t\t\t%.3f msec\n", dt);
        minTimeOpenacc = std::min(minTimeOpenacc, dt);
    }

    printf("[stencil openacc-m]:\t\t%.3f msec\n", minTimeOpenacc);


    //printf("\t\t\t\t(%.2fx speedup from ISPC, %.2fx speedup from ISPC + tasks)\n", \
           minTimeSerial / minTimeISPC, minTimeSerial / minTimeISPCTasks);

    // Check for agreement
    /*
    int offset = 0;
    int n_errors = 0;
    for (int z = 0; z < Nz; ++z){
        for (int y = 0; y < Ny; ++y){
            for (int x = 0; x < Nx; ++x, ++offset){
                float error = fabsf((Aserial[1][offset] - Aispc[1][offset]) /
                                    Aserial[1][offset]);
                if (error > 1e-4){
                    //printf("Error @ (%d,%d,%d): ispc = %f, serial = %f\n",\
                           x, y, z, Aispc[1][offset], Aserial[1][offset]);
                    n_errors++;
                }

                float error2 = fabsf((Aserial[1][offset] - Aopenacc[1][offset]) /
                                    Aserial[1][offset]);
                if (error2 > 1e-4){
                    //printf("Error @ (%d,%d,%d): openacc = %f, serial = %f\n",\
                           x, y, z,\
                           Aopenacc[1][offset],\
                           Aserial[1][offset]);
                    n_errors++;
                }
            }
        }
    }

    if(n_errors) printf("%d errors found out of %d.\n", n_errors, Nz*Ny*Nx);
    */

    return 0;
}
