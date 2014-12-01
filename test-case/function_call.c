

float    maximum(float a, float b)
{
    return (a>b)?a:b;
}
float funct(float a, float b)
{
    return (a>b)?maximum(a,b):b;
}



int SIZE=1024;

int main()
{
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 

    float a[SIZE], b[SIZE], c[SIZE];
    int i;
    for(i=0; i<2*SIZE; i++)
    {
        a[i%SIZE]=i;
        b[i%SIZE]=a[(i*13)%SIZE];
        c[i%SIZE]=0;
    }

    #pragma acc kernels copyin(a,b) copyout(c)
    #pragma acc loop independent 
    for(int i=0; i<SIZE; i++)
    {
        c[i] = funct (a[i], b[i]);
        //c[i] = a[i]>b[i]?a[i]:b[i];
    }

    for (i = 0; i < SIZE; ++i) {
            if(c[i]!= funct(a[i],b[i])) {
                fprintf(stderr,"Error %d %16.10f!=%16.10f \n", i, c[i], funct(a[i],b[i]));
                return -1;
            }
    }
    fprintf(stderr,"'function call in kernels region' test was successful!\n");
    return 0;
}
