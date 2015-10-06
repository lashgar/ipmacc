#include <malloc.h>
#include <time.h>
#include <openacc.h>
//#include <accelmath.h>
#include <math.h>

#define SIZE 30
int main()
{
    int i=0;

    float a[SIZE];
    float b[SIZE];
    float c[SIZE];
    float seq[SIZE];
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
    float sum=0, maX;
    int k;
    for(k=0; k<1; k++){
        printf("Calculation on GPU ... ");
        tic = clock();
        sum=0;
        maX=-1;
        #pragma acc data copy(a,b,c)
        {
            #pragma acc kernels copyout(maX)
            {
                #pragma acc loop independent private(maX,sum)
                for (i = 0; i < SIZE; ++i)
                {
                    float x=0;
                    x = a[i] + b[i];
                    sum= sum + x;
                    c[i] = x;
                    maX = x;
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
    float cpuMax=-1, cpuSum=0;
    for (i = 0; i < SIZE; ++i) {
        //F
        seq[i] = a[i] + b[i] ;
        if(c[i]>cpuMax)
            cpuMax=c[i];
        cpuSum+=c[i];
        if(c[i]!= seq[i]) {
            printf("Error %d %16.10f!=%16.10f \n", i, c[i], seq[i]);
            exit(1);
        }
    }//F
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    printf(" max on GPU: %6.4f, on CPU: %6.4f \n",maX,cpuMax);
    printf(" sum on GPU: %6.4f, on CPU: %6.4f \n",sum,cpuSum);

    if(maX == cpuMax && sum==cpuSum){
        fprintf(stderr, "OpenACC reduction test was successful!\n");
        return 0;
    }else{
        fprintf(stderr, " max on GPU: %6.4f, on CPU: %6.4f \n",maX,cpuMax);
        fprintf(stderr, " sum on GPU: %6.4f, on CPU: %6.4f \n",sum,cpuSum);
        fprintf(stderr, "Error! OpenACC reduction test was failed!\n");
        return -1;
    }

}
