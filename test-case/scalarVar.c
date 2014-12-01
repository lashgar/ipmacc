#include <malloc.h>
#include <time.h>
#include <openacc.h>
#include <math.h>

#define SIZE 1024
int main()
{
    int i;

    float a[SIZE];
    float b[SIZE];
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 

    for (i = 0; i < SIZE; ++i)
    {
            a[i] = (float)i ;
            b[i] = (float)i;
    }

    float pi=3.14159265359;
    float sum=0;

    unsigned long long int tic, toc;
    // Compute vector Add
    int k;
    for(k=0; k<3; k++){
        //C
        printf("Calculation on GPU ... ");
        tic = clock();
        sum=0;

        #pragma acc data copy(a[0:SIZE],pi) copyout(b[0:SIZE])
        {
            # pragma acc kernels 
            {
                #pragma acc loop independent reduction(+:sum)
                {
                    for (i = 0; i < SIZE; ++i) {
                        float k=0;
                        k = a[i]*pi;
                        b[i]=k;
                        sum+=k;
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
    printf("Calculation on CPU ... ");
    tic = clock();
    float sumCPU=0;
    for (i = 0; i < SIZE; ++i) {
            sumCPU+=a[i]*pi;
            if(b[i]!= (a[i]*pi)) {
                printf("Error %d %16.10f!=%16.10f \n", i, b[i], a[i]*pi);
                exit(1);
            }
    }
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    printf(" Sum reduction on CPU:%6.4f GPU:%6.4f\n",sumCPU,sum);

    if(sumCPU==sum){
        fprintf(stderr,"OpenACC scalar value transfer test was successful!\n");
        return 0;
    }else{
        fprintf(stderr, " Sum reduction on CPU:%6.4f GPU:%6.4f\n",sumCPU,sum);
        fprintf(stderr,"Error! OpenACC scalar value transfer test was failed!\n");
        return -1;
    }

}
