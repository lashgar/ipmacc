#include <malloc.h>
#include <time.h>
#include <openacc.h>
#include <math.h>

int inc_step(){
    return 2;
}

#define SIZE 1024
int main()
{
    int i;

    float a[SIZE];
    float b[SIZE];
    float c[SIZE];
    float seq[SIZE];
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
            a[i] = (float)i ;
            b[i] = (float)2*i;
            c[i] = 0.0f;
    }// B

    unsigned long long int tic, toc;
    // Compute vector Add
    int d[1]={0};
    int k;
    for(k=0; k<3; k++){
        //C
        printf("Calculation on GPU ... ");
        tic = clock();
        #pragma acc data pcopyin(a[0:SIZE],b[0:SIZE]) pcopyout(c[0:SIZE]) pcopy(d[0:1])
        {
            # pragma acc kernels 
            {
                #pragma acc loop independent 
                {
                    for (i = 0; i < SIZE; ++i) {
                        #pragma acc atomic capture
                        {
                            d[0]+=inc_step();
                        } 
                        c[i] = a[i] + b[i] ;
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
    printf("Calculation on CPU ... ");
    tic = clock();
    for (i = 0; i < SIZE; ++i) {
            seq[i] = a[i] + b[i] ;
            if(c[i]!= seq[i]) {
                fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i], seq[i]);
                return -1;
            }
    }
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    printf("atomic sum> %d (should be %d)\n", d[0], 3*SIZE*inc_step());
    if(d[0]==3*SIZE*inc_step()){
        fprintf(stderr,"OpenACC atomic operation test was successful!\n");
    }else{
        fprintf(stderr,"OpenACC atomic operation test failed!\n");
    }
    return 0;
}
