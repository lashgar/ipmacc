#define char int8
#define fabsf(f) abs(f)
#define floorf(f) floor(f)
#define logf(f) log(f)
#define sqrtf(f) sqrt(f)
#define expf(f) exp(f)
#define powf(f,p) pow(f,p)




task void __generated_kernel_region_0(uniform float a[],uniform float c[],uniform float b[],uniform unsigned int SIZE){
    int __kernel_getuid_x=programIndex;
    {
        {
            {
                uniform int __ispc_loop_initial = 0;
                foreach(i= __ispc_loop_initial ... ((SIZE)))
                {
                    c [i] = a [i] + b [i];
                }

            }
        }
    }

}

export void __generated_kernel_launch_0(uniform float a[],uniform float c[],uniform float b[],uniform unsigned int SIZE){
    launch [1] __generated_kernel_region_0(a,c,b,SIZE);
}
