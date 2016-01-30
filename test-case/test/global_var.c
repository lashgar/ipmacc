#include <malloc.h>
#include <time.h>
#include <openacc.h>
#include <math.h>

#define SIZE 8199

float glb_var = 192;


int main()
{
    int i;

    float c[SIZE];
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    acc_list_devices_spec( acc_device_nvocl );
    #endif 


    // Initialize matrices.
    for (i = 0; i < SIZE; ++i) {
            c[i] = 0.0f;
    }

        #pragma acc data pcopyout(c[0:SIZE])
        {
            # pragma acc kernels 
            {
                #pragma acc loop independent 
                {
                    for (i = 0; i < SIZE ; ++i) {
                        c[i] = glb_var;
                    }
                }
            }
        }

    for (i = 0; i < SIZE; ++i) {
            if(c[i]!= 192.0) {
                fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i], 192.0);
                return -1;
            }
    }

    fprintf(stderr,"OpenACC global variable test was successful!\n");
    return 0;
}
