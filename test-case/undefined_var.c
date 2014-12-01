#include <malloc.h>
#include <time.h>
#include <openacc.h>
//#include <accelmath.h>
#include <math.h>

#define SIZE 1000
int main()
{
    int i;

    float a[SIZE];
    float b[SIZE];
    float c[SIZE];
    float seq[SIZE];
    //acc_init( acc_device_nvidia );
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 


    // Initialize matrices.
    for (i = 0; i < SIZE; ++i) {
        //B
            a[i] = (float)i ;
            b[i] = (float)2*i;
            c[i] = 0.0f;
    }// B

    unsigned long long int tic, toc;
    // Compute vector Add
    int k;
    for(k=0; k<3; k++){
        //C
        printf("Calculation on GPU ... ");
        tic = clock();

            #pragma acc kernels present_or_copyin(a,b) present_or_copyout(c) create(seq) async if(1)
            //#pragma acc kernels copyin(a,b) copyout(c) create(seq) async if(1)
            {
                #pragma acc loop independent
                {
                    for (i = 0; i < SIZE; ++i) {
                        //D
                                c[i] = a[i] + b[i] ;
                    }//D
                }
            }
        toc = clock();
        printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    }//C

    // ****************
    // double-check the OpenACC result sequentially on the host
    // ****************
    // Perform the add
    printf("Calculation on CPU ... ");
    tic = clock();
    for (i = 0; i < SIZE; ++i) {
        //F
            seq[i] = a[i] + b[i] ;
            if(c[i]!= seq[i]) {
                fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i], seq[i]);
                exit(1);
            }
    }//F
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);

    fprintf(stderr,"OpenACC vector add test was successful!\n");

    return 0;
}
