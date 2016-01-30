#include <stdio.h>

// FWIW, changing the basic data type to `double' won't pass the ISPC test!
#define DATATYPE float

DATATYPE glb_var = 7.99;


inline DATATYPE fcn_4()
{
    return 8.3;
}

inline DATATYPE fcn_3(DATATYPE arg1, DATATYPE arg2)
{
    DATATYPE fact = 13.4;
    return arg1*arg1*arg2*fact;
}

inline DATATYPE fcn_2(DATATYPE arg1, DATATYPE arg2)
{
    return arg1*arg2;
}

DATATYPE fcn_1(int arg1, DATATYPE arg2, DATATYPE *arg3)
{
    return arg3[arg1] + fcn_2(fcn_4(), arg2) + fcn_3(9.4, arg2);
}

void kernel_1(DATATYPE *in1, DATATYPE *out1, int size)
{
    int i = 0;
    #pragma acc kernels pcopyin(in1[0:size]) pcopyout(out1[0:size])
    #pragma acc loop independent 
    for(i=0; i<size; i++){
        out1[i] = fcn_1(i, size*1.1, in1);
    }
}

void kernel_2(DATATYPE *in1, DATATYPE *out1, int size)
{
    int i = 0;
    #pragma acc kernels pcopyin(in1[0:size]) pcopyout(out1[0:size])
    #pragma acc loop independent 
    for(i=0; i<size; i++){
        out1[i] = fcn_1(i, size*14.14, in1);
    }
}

int main()
{
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    acc_list_devices_spec( acc_device_nvocl );
    #endif 

    int size = 8195;
    DATATYPE a[size], b[size];
    int i;
    for(i=0; i<size; ++i){
        a[i] = i;
    }
    kernel_1(a, b, size);
    for(i=0; i<size; ++i){
        if(b[i]!=fcn_1(i, size*1.1, a)){
            printf("mistmatch at %i: %f != %f\n", i, b[i], fcn_1(i, size*1.1, a));
            return -1;
        }
    }
    printf("Nested function test passed!\n");
    return 0;
}
