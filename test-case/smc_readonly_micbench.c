#include <stdio.h>
#include <malloc.h>
#include <sys/time.h>
#include <unistd.h>
#include "openacc.h"
#include "cutil.h"

int main(int argc, char **argv)
{
#ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
#endif 
#ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
#endif 

    int iter=1024;

    if(argc!=2){
        printf("usage: iteration (integer number)\n");
        return 0;
    }else{
        sscanf(argv[1],"%d",&iter);
        printf("iterations: %d\n",iter);
    }


    int i=0, size=4096;
    int *a=(int*)malloc(sizeof(int)*size);
    for(i=0; i<size; ++i)
    {
        a[i]=i;
    }

    double mtime=0.0;
    unsigned int timer = 0;
    CUT_SAFE_CALL( cutCreateTimer( &timer));
    #pragma acc data copy(a[0:size])
    for(int k=0; k<30; ++k){
        CUT_SAFE_CALL( cutStartTimer( timer));
        #pragma acc kernels 
        #pragma acc loop independent smc(a[0:size:READ_ONLY:0:1:1:true])
        for(i=0; i<size; ++i)
        {
            int j, partial_sum=0;
            for(j=0; j<iter; ++j)
            {
                partial_sum += (i>0)?a[i-1]:0;
                partial_sum += (i<(size-1))?a[i+1]:0;
                partial_sum = partial_sum/2;
            }
            a[i]=partial_sum;
        }
        CUT_SAFE_CALL( cutStopTimer( timer));
        mtime += cutGetTimerValue( timer);
    }
    CUT_SAFE_CALL( cutDeleteTimer( timer));

    printf("Elapsed time: %6.4f milliseconds\n",mtime/30.0);

}
