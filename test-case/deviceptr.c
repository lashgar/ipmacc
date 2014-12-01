#include <malloc.h>
#include <time.h>
#include <openacc.h>
//#include <accelmath.h>
#include <math.h>

#define SIZE 1024
int main()
{
    int i=0;

    float a[SIZE];
    float b[SIZE];
    float c[SIZE];
    float seq[SIZE];
    //acc_init( acc_device_nvidia );


    // Initialize matrices.
    for (i = 0; i < SIZE; ++i) {
        //B
        a[i] = (float)i ;
        b[i] = (float)2*i;
        c[i] = 0.0f;
    }// B

    float *devp=NULL;
    cudaMalloc((void**)&devp, sizeof(float)*SIZE);
    cudaMemset(devp, 0, sizeof(float)*SIZE);

    unsigned long long int tic, toc;
    // Compute vector Add
    int k;
    for(k=0; k<3; k++){
        //C
        printf("Calculation on GPU ... ");
        tic = clock();

        #pragma acc data pcopyin(a,b) pcopyout(c,seq) deviceptr(devp)
        {
            #pragma acc kernels 
            {
                #pragma acc loop independent
                {
                    for (i = 0; i < SIZE; ++i) {
                        //D
                        c[i] = a[i] + b[i] ;
                        seq[i]=devp[i];
                    }//D
                }
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
    for (i = 0; i < SIZE; ++i)
    {
        //F
        //seq[i] = a[i] + b[i] ;
        float f=a[i]+b[i];
        if(c[i]!=f || seq[i]!=0)
        {
            fprintf(stderr,"Error: [%d] %16.10f!=%16.10f or %16.10f!=0 \n", i, c[i], a[i]+b[i], seq[i]);
            exit(1);
        }
    }//F
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);

    fprintf(stderr,"OpenACC device pointer (CUDA cooperation) test was successful!\n");

    return 0;
}
