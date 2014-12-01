#include <stdio.h>
#include <math.h>

#define FUNC sqrt
#define SIZE 32

int main()
{

    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 

    int i=0;
    float in[SIZE], hout[SIZE], dout[SIZE];
 
    for(i=0; i<SIZE; i++)
    {
        in[i]=exp(i+SIZE)/exp(2*SIZE);
    }

    #pragma acc kernels copyin(in) copyout(dout)
    #pragma acc loop independent
    for(i=0; i<SIZE; i++)
    {
        dout[i]=FUNC(in[i]);
    }
    
    for(i=0; i<SIZE; i++)
    {
        hout[i]=FUNC(in[i]);
    }

    for(i=0; i<SIZE; i++)
    {
        printf("%28.26f\t<>host  [%28.26f]\n\t\t\t\t  device[%28.26f]\n\n",in[i],hout[i],dout[i]);
    }

    return 0;
}
