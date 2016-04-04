#define char int8
#define fabsf(f) abs(f)
#define floorf(f) floor(f)
#define logf(f) log(f)
#define sqrtf(f) sqrt(f)
#define expf(f) exp(f)
#define powf(f,p) pow(f,p)




task void __generated_kernel_region_0(uniform float a[],uniform float c[],uniform float b[],uniform unsigned int __ispc_n_threads,uniform unsigned int SIZEX,uniform unsigned int SIZEZ,uniform unsigned int SIZEY){
    int __kernel_getuid_x=programIndex;
    int i;
    int j;
    int l;
    {
        {
            {
                for(int l=( 0) +taskIndex0 ; l < SIZEZ;l=l+__ispc_n_threads
                   )
                {
                    {
                        {
                            {
                                uniform int __ispc_loop_initial = 0;
                                foreach( i= __ispc_loop_initial ... ((SIZEX)), j= 0 ... SIZEY)
                                {
                                    int idx = l * SIZEX * SIZEY + j * SIZEX + i;
                                    c [idx] = a [idx] + b [idx];
                                }

                            }
                        }

                    }
                }

            }
        }
    }

}export void __generated_kernel_launch_0(uniform float a[],uniform float c[],uniform float b[],uniform unsigned int __ispc_n_threads,uniform unsigned int SIZEX,uniform unsigned int SIZEZ,uniform unsigned int SIZEY){launch [__ispc_n_threads] __generated_kernel_region_0(a,c,b,__ispc_n_threads,SIZEX,SIZEZ,SIZEY);}
