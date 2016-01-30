//#include <malloc.h>
//#include <time.h>
//#include <openacc.h>
//#include <math.h>

#define SIZE 8199

float glb_var = 192;

float glb_arr[4] = {0, 1, 2, 3};

float fcn3(float* arg1){
    return 1;
}

float fcn2(float arg1){
    return arg1*glb_var*glb_arr[1];
}

float fcn1(){
    return fcn2(13.1);
}

int main()
{
    int i;

    float c[SIZE];
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
        c[i] = 0.0f;
    }

#pragma acc data pcopyout(c[0:SIZE])
#pragma acc kernels 
#pragma acc loop independent 
    for (i = 0; i < SIZE ; ++i) {
        float jj = 1;
        c[i] = fcn1() * i * fcn3(c);
    }

    for (i = 0; i < SIZE; ++i) {
        if(c[i]!= (fcn1()*i)) {
            fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i], (fcn1()*i));
            return -1;
        }
    }

    fprintf(stderr,"OpenACC global variable test was successful!\n");
    return 0;
}
