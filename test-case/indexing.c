#include <malloc.h>
#include <time.h>
#include <openacc.h>
//#include <accelmath.h>
#include <math.h>

#define LEN 32
#define SIZE LEN*LEN
int main()
{
    int i;

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

    unsigned long long int tic, toc;
    // Compute vector Add
    int k,j,l;
    for(k=0; k<3; k++){
        //C
        printf("Calculation on GPU ... ");
        tic = clock();

#pragma acc data pcopyin(a[0:SIZE],b[0:SIZE]) pcopy(c[0:SIZE])
        {
#pragma acc kernels
            {
#pragma acc loop independent 
                {
                    for (i = 0; i < LEN; ++i) {
#pragma acc loop independent 
                        {
                            for(j=0; j<LEN; j++){
                                float sum=0;
                                for(l=0; l<LEN; l++){
                                    sum+=l*2;
                                }
                                c[i*LEN+j]=j+sum-sum;
                            }
                        }
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
    for (i = 0; i < LEN; ++i) {
        for(j=0; j<LEN; j++){
            printf("%4.2f ",c[i*LEN+j]);
        }
        printf("\n");

    }//F
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);

    printf(stderr, "OpenACC indexing was successful!\n");

    return 0;
}
