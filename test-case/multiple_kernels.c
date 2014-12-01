#include <stdio.h>
#include <malloc.h>

int main(){
    int SIZE=1024;
    float *a=(float*)malloc(sizeof(float)*SIZE);
    float *b=(float*)malloc(sizeof(float)*SIZE);
    float *c=(float*)malloc(sizeof(float)*SIZE);
    int i,k,j;

    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 

    #pragma acc kernels create(a[0:SIZE],b[0:SIZE],c[0:SIZE]) copyout(a[0:SIZE],b[0:SIZE],c[0:SIZE])
    {
        #pragma acc loop independent
        for(i=0; i<SIZE; i++){
            a[i]=i;
            b[i]=SIZE-i;
        }
    }

    #pragma acc kernels present(a,b,c) copyout(c[0:SIZE])
    {
        #pragma acc loop independent
        for(i=0; i<SIZE; i++){
            c[i]=a[i]+b[i];
        }
    }

    for(i=0; i<SIZE; i++){
        if(c[i]!=(a[i]+b[i])){
            fprintf(stderr,"failed to perform the sum at %d. %6.4f + %6.4f =%6.4f\n",i,a[i],b[i],c[i]);
            return -1;
        }
    }
    fprintf(stderr,"Multiple kernels test was successfull!\n");
    return 0;
}


