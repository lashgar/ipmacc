#include <malloc.h>
#include <time.h>
#include <assert.h>
#include <openacc.h>
#include <math.h>
#include "../timing.h"

//#define SIZEX 8192
//#define SIZEY 1
//#define SIZEZ 1


int main(int argc, char* argv[])
{
    int i, j, l;
    unsigned int SIZEX = 0;
    unsigned int SIZEY = 0;
    unsigned int SIZEZ = 0;
    if(argc==4){
        sscanf(argv[1], "%d", &SIZEX);
        sscanf(argv[2], "%d", &SIZEY);
        sscanf(argv[3], "%d", &SIZEZ);
    }else{
        printf("usage: %s xdim ydim zdim\n",argv[0]);
        return -1;
    }

    unsigned int SIZE = SIZEX*SIZEY*SIZEZ;
    assert(SIZE>0);
    printf("allocation size> %d\n", SIZE);

    float *a = (float*)malloc(sizeof(float)*SIZE);
    float *b = (float*)malloc(sizeof(float)*SIZE);
    float *c = (float*)malloc(sizeof(float)*SIZE);


    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    //#define DEVICE_TYPE acc_device_intelocl // alternative: acc_device_nvocl 
    #define DEVICE_TYPE acc_device_nvocl // alternative: acc_device_intelocl
    printf("compiled for ocl\n");
    acc_init( DEVICE_TYPE );
    acc_list_devices_spec( DEVICE_TYPE );
    #endif 


    // Initialize matrices.
    for (i = 0; i < SIZEX*SIZEY*SIZEZ; ++i) {
        a[i] = (float)i ;
        b[i] = (float)2*i;
        c[i] = 0.0f;
    }

    // Compute vector Add
    int k;
    double revsum = 0;
    int iter = 30;
    #pragma acc data pcopyin(a[0:SIZE],b[0:SIZE]) pcopyout(c[0:SIZE])
    for(k=0; k<iter; k++){
        reset_and_start_timer();
        #pragma acc kernels 
        #pragma acc loop independent
        for (l = 0; l < SIZEZ ; ++l) {
            #pragma acc loop independent 
            for (j = 0; j < SIZEY ; ++j) {
                #pragma acc loop independent 
                for (i = 0; i < SIZEX ; ++i) {
                    int idx = l*SIZEX*SIZEY + j*SIZEX + i;
                    c[idx] = a[idx] + b[idx];
                }
            }
        }
        double dt = get_elapsed_msec();
        revsum += 1.0/dt;
        printf("@time of openacc run:\t\t\t%.3f msec\n", dt);
    }
    printf("harmonic mean openacc run> %.3f msec\n", iter/revsum);

    // ****************
    // double-check the OpenACC result sequentially on the host
    // ****************
    // Perform the add
    for (i = 0; i < SIZEX*SIZEY*SIZEZ; ++i) {
        if(c[i]!=(a[i] + b[i])){
            fprintf(stdout,"Error %d %16.10f!=%16.10f \n", i, c[i], a[i]+b[i]);
            return -1;
        }
    }

    fprintf(stdout,"OpenACC vectoradd test was successful!\n");
    return 0;
}
