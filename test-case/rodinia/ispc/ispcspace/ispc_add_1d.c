#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#ifdef __cplusplus
#include "openacc_container.h"
#endif

// no header for ISPC

#include <malloc.h>
#include <time.h>
#include <assert.h>
#include <openacc.h>
#include <math.h>
#include "../timing.h"






 extern "C" void __generated_kernel_launch_0(float  a[],float  c[],float  b[],unsigned int  SIZE);
 
int main(int argc, char* argv[])
{
  int i;
  unsigned int SIZEX = 0;
  unsigned int SIZEY = 0;
  unsigned int SIZEZ = 0;
  if (argc == 4) {
    sscanf(argv [1], "%d", &SIZEX);
    sscanf(argv [2], "%d", &SIZEY);
    sscanf(argv [3], "%d", &SIZEZ);
  }else{
    printf("usage: %s xdim ydim zdim\n", argv [0]);
    return -1;
  }

  unsigned int SIZE = SIZEX * SIZEY * SIZEZ;
  assert(SIZE > 0);
  printf("allocation size> %d\n", SIZE);

  float *a = (float*)malloc(sizeof(float) * SIZE);
  float *b = (float*)malloc(sizeof(float) * SIZE);
  float *c = (float*)malloc(sizeof(float) * SIZE);


    #ifdef __NVCUDA__
  acc_init(acc_device_nvcuda);
    #endif
    #ifdef __NVOPENCL__
  
    #define DEVICE_TYPE acc_device_nvocl 
  printf("compiled for ocl\n");
  acc_init(DEVICE_TYPE);
  acc_list_devices_spec(DEVICE_TYPE);
    #endif


  
  for (i = 0; i < SIZE; ++i) {
    a [i] = (float)i;
    b [i] = (float)2 * i;
    c [i] = 0.0f;
  }

  
  int k;
  double revsum = 0;
  int iter = 30;
    

	ipmacc_prompt((char*)"IPMACC: memory allocation c\n");
// ISPC host and device are the same, skipping memory allocation
ipmacc_prompt((char*)"IPMACC: memory allocation a\n");
// ISPC host and device are the same, skipping memory allocation
ipmacc_prompt((char*)"IPMACC: memory allocation b\n");
// ISPC host and device are the same, skipping memory allocation
	ipmacc_prompt((char*)"IPMACC: memory copyin a\n");
// ISPC host and device are the same, skipping copyin
ipmacc_prompt((char*)"IPMACC: memory copyin b\n");
// ISPC host and device are the same, skipping copyin


{


  
		for(k = 0; k < iter; k++)
 {
    reset_and_start_timer();
        


/* kernel call statement*/
{

unsigned int __ispc_n_threads = sysconf(_SC_NPROCESSORS_ONLN); // acc_get_n_cores(acc_device_intelispc);
if(getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching ISPC kernel> %d threads + SIMD \n", __ispc_n_threads);
__generated_kernel_launch_0(a,c,b,SIZE);
}
/* kernel call statement*/
// ISPC target is synchronized with CPU
// skipping synchronization



    double dt = get_elapsed_msec();
    revsum += 1.0 / dt;
    printf("@time of openacc run:\t\t\t%.3f msec\n", dt);
  }


}
	ipmacc_prompt((char*)"IPMACC: memory copyout c\n");
// ISPC host and device are the same, skipping copyout



  printf("harmonic mean openacc run> %.3f msec\n", iter / revsum);

  
  
  
  
  for (i = 0; i < SIZE; ++i) {
    if (c [i] != (a [i] + b [i])) {
      fprintf(stdout, "Error %d %16.10f!=%16.10f \n", i, c [i], a [i] + b [i]);
      return -1;
    }
  }

  fprintf(stdout, "OpenACC vectoradd test was successful!\n");
  return 0;
}



