#include <stdio.h>
#include <malloc.h>
#include "openacc.h"

int main()
{
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    #endif 

    int i=0, size=4096;
    int *a=(int*)malloc(sizeof(int)*size);
    int *b=(int*)malloc(sizeof(int)*size);
    int sum=0;
    for(i=0; i<size; ++i)
    {
        a[i]=i;
    }

    #pragma acc kernels copy(a[0:size],b[0:size])
    #pragma acc loop independent reduction(+:sum) smc(b[0:size:READ_WRITE:0:1:1:false], a[0:size:READ_ONLY:0:1:1:false])
    for(i=0; i<size; ++i)
    {
        int j, partial_sum=0;
        for(j=0; j<1024; j++)
        {
            partial_sum += (i>0)?a[i-1]:0;
            partial_sum += (i<(size-1))?a[i+1]:0;
            partial_sum = partial_sum/2 + b[i];
        }
        b[i]=a[i]; //partial_sum+a[i];
        b[i]=b[i]+b[i];

        //write_(b,i,partial_sum);
        sum += (a[i]+partial_sum);
    }

    printf("sum is: %d\nb[%d] is %d\n",sum,109,b[109]);
}
