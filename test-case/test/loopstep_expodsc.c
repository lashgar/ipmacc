#include <malloc.h>
#include <time.h>
#include <openacc.h>
#include <math.h>

#define SIZE 8199
int main()
{
    int i;

    float a[SIZE];
    float b[SIZE];
    float c[SIZE];
    float seq[SIZE];
    /*
    float Papi[SIZE][SIZE];
    float *onedim;
    float *twodim;
    float temp[3]={a[0],b[0],c[0]};
    */
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    acc_list_devices_spec( acc_device_nvocl );
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
        #pragma acc data pcopyin(a[0:SIZE],b[0:SIZE]) pcopyout(c[0:SIZE])
        {
            # pragma acc kernels 
            {
                #pragma acc loop independent 
                {
                    for (i = SIZE-1; i > 0 ; i=i/3) {
                        c[i] = a[i] + b[i] ;
                    }
                }
            }
        }
        toc = clock();
        printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    }

    // ****************
    // double-check the OpenACC result sequentially on the host
    // ****************
    // Perform the add
    printf("Calculation on CPU ... ");
    tic = clock();
    for (i = SIZE-1; i > 0 ; i=i/3) {
            seq[i] = a[i] + b[i] ;
            if(c[i]!= seq[i]) {
                fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i], seq[i]);
                return -1;
            }
    }
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);

    fprintf(stderr,"OpenACC vectoradd test was successful!\n");
    return 0;
}
