#include <malloc.h>
#include <time.h>
#include <openacc.h>
#include <math.h>

#define SIZE 1025

int main()
{
    int i=0;

    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 
    
    size_t free=-1, total=-1;
    acc_get_mem_info(&free, &total);
    printf("device memory info> free/total %d/%d [%6.4f percent free]\n",free,total,free/(float)total*100);

    float a[SIZE];
    float b[SIZE];
    float c[SIZE];

    // Initialize matrices.
    for (i = 0; i < SIZE; ++i) {
        //B
        a[i] = (float)i ;
        b[i] = (float)2*i;
        c[i] = 0.0f;
    }// B

    unsigned long long int tic, toc;
    // Compute vector Add
    float sum=0, maX;
    int k;
    
#pragma acc enter data copyin(a,b) create(c)

    for(k=0; k<3; k++){
        printf("Calculation on GPU ... ");
        tic = clock();
        sum=0;
        maX=-1;
        #pragma acc kernels present(a,b,c)
        #pragma acc loop independent 
        for (i = 0; i < SIZE; ++i) {
            float x=0;
            x = a[i] + b[i] ;
            c[i] = x;
        }
        toc = clock();
        printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    }

#pragma acc exit data copyout(c)

    // ****************
    // double-check the OpenACC result sequentially on the host
    // ****************
    // Perform the add
    printf("Calculation on CPU ... ");
    tic = clock();
    float cpuMax=-1, cpuSum=0;
    for (i = 0; i < SIZE; ++i) {
        //F
        if(c[i]!= (a[i]+b[i])) {
            fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i], a[i]+b[i]);
            exit(1);
        }
    }//F
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    fprintf(stderr,"OpenACC API test was successful!\n");

    printf("Shutting down the device...");
    acc_shutdown(acc_device_nvcuda);
    printf("[done]\n");

    return 0;
}
