#include <malloc.h>
#include <time.h>
#include <openacc.h>
#include <math.h>

typedef struct {
    float r;
    float c;
} user_nested_type_t;

typedef struct user_def_type_s {
    float x;
    float y;
    int a, b, c;
    user_nested_type_t k;
} user_def_type_t;

#define SIZE 8199
int main()
{
    int i;

    user_def_type_t a[SIZE];
    user_def_type_t b[SIZE];
    user_def_type_t c[SIZE];
    user_def_type_t seq[SIZE];
    /*
    float Papi[SIZE][SIZE];
    float *onedim;
    float *twodim;
    float temp[3]={a[0],b[0],c[0]};
    */
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    acc_list_devices_spec( acc_device_nvocl );
    #endif 


    // Initialize matrices.
    for (i = 0; i < SIZE; ++i) {
        //B
            a[i].x = (float)i ;
            b[i].x = (float)2*i;
            c[i].x = 0.0f;
    }// B

    unsigned long long int tic, toc;
    // Compute vector Add
    int k;
    for(k=0; k<3; k++){
        //C
        printf("Calculation on accelerator ... ");
        tic = clock();
        #pragma acc data pcopyin(a[0:SIZE],b[0:SIZE]) pcopyout(c[0:SIZE])
        {
            # pragma acc kernels 
            {
                #pragma acc loop independent 
                {
                    for (i = 0; i < SIZE ; ++i) {
                        c[i].x = a[i].x + b[i].x ;
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
    // Perform the add
    printf("Calculation on host ... ");
    tic = clock();
    for (i = 0; i < SIZE; ++i) {
            seq[i].x = a[i].x + b[i].x ;
            if(c[i].x!= seq[i].x) {
                fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i].x, seq[i].x);
                return -1;
            }
    }
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);

    fprintf(stderr, "[test succeeded]\n");
    return 0;
}
