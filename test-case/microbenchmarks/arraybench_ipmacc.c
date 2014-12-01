#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#include <CL/cl.h>
extern cl_int __ipmacc_clerr ;
extern cl_context __ipmacc_clctx ;
extern size_t __ipmacc_parmsz;
extern cl_device_id* __ipmacc_cldevs;
extern cl_command_queue __ipmacc_command_queue;























#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define __STDC_LIMIT_MACROS
#include <stdint.h> 

#include <climits>
#include "arraybench.h"
#include <sys/time.h>

double btest [IDA];
double atest [IDA];
int nthreads, delaylength, innerreps;
double times [OUTERREPS + 1], reftime, refsd;

time_t starttime = 0;
timeval tim;



int main(int argv, char **argc)
{
#ifdef __NVCUDA__
  acc_init(acc_device_nvcuda);
#endif
#ifdef __NVOPENCL__
  acc_init(acc_device_nvocl);
  
#endif



  printf(" *******************************************************\n");

  delaylength = 500;
  innerreps = 100;
  
  

  
  

  
  

#ifdef OMPVER2
  
  
#endif

  
  copyintest();

  
  copyouttest();

  
  createtest();


  
  reductiontest();

  
  kerneltest();


  
  



  delaylength = 500;
  innerreps = 100;
}

static int firstcall = 1;


double get_time_of_day_()
{
  struct timeval ts;

  double t;

  int err;

  err = gettimeofday(&ts, NULL);

  t = (double)(ts.tv_sec - starttime) + (double)ts.tv_usec * 1.0e-6;

  return t;
}

void init_time_of_day_()
{
  struct  timeval ts;
  int err;

  err = gettimeofday(&ts, NULL);
  starttime = ts.tv_sec;
}

double getclock(void)
{
  double time;
  double get_time_of_day_(void);
  void init_time_of_day_(void);

  if (firstcall) {
    init_time_of_day_();
    firstcall = 0;
  }
  time = get_time_of_day_();
  return time;
}


void delay(int delaylength, double a [1])
{
  int i;
  a [0] = 1.0;
  for (i = 0; i < delaylength; i++) {
    a [0] += i;
  }
  
}

void refer()
{
  int j, k;
  int i = 0;
  double start;
  double meantime, sd, hm;
  double a [1];
  

  printf("\n");
  printf("--------------------------------------------------------\n");
  printf("Computing reference time 1\n");

  for (k = 0; k <= OUTERREPS; k++) {
    start = getclock();
    for (j = 0; j < innerreps; j++) {
      delay(delaylength, a);
      i++;
    }
    times [k] = (getclock() - start) * 1.0e6 / (double)innerreps;
  }

  stats(&meantime, &sd, &hm);

  
  printf("Reference_time_1 =                        %10.3f microseconds +/- %10.3f\n", hm, CONF95 * sd);

  reftime = meantime;
  refsd = sd;
}

void testfirstprivnew()
{
  int n, j, k;
  double start;
  double meantime, sd;
  

  n = IDA;
  printf("\n");
  printf("--------------------------------------------------------\n");
  printf("Computing FIRSTPRIVATE %d time\n", n);

  for (k = 0; k <= OUTERREPS; k++) {
    start = getclock();
    
    for (j = 0; j < innerreps; j++) {
      
      {
        delay(delaylength, atest);
      }
    }
    times [k] = (getclock() - start) * 1.0e6 / (double)innerreps;
  }

  

  
  printf("FIRSTPRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95 * sd);
  printf("FIRSTPRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime - reftime, CONF95 * (sd + refsd));
}

void testprivnew()
{
  int n, j, k;
  double start;
  double meantime, sd;
  

  n = IDA;
  printf("\n");
  printf("--------------------------------------------------------\n");
  printf("Computing PRIVATE %d time\n", n);

  for (k = 0; k <= OUTERREPS; k++) {
    start = getclock();
    for (j = 0; j < innerreps; j++) {
      
      {
        delay(delaylength, atest);
      }
    }
    times [k] = (getclock() - start) * 1.0e6 / (double)innerreps;
  }

  

  
  printf("PRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95 * sd);
  printf("PRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime - reftime, CONF95 * (sd + refsd));
}

#ifdef OMPVER2
void testcopyprivnew()
{
  int n, j, k;
  double start;
  double meantime, sd;
  
  n = IDA;
  printf("\n");
  printf("--------------------------------------------------------\n");
  printf("Computing COPYPRIVATE %d time\n", n);

  for (k = 0; k <= OUTERREPS; k++) {
    start = getclock();
    for (j = 0; j < innerreps; j++) {
      
      {
        delay(delaylength, btest);
      }
    }
    times [k] = (getclock() - start) * 1.0e6 / (double)innerreps;
  }

  

  printf("COPYPRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95 * sd);
  printf("COPYPRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime - reftime, CONF95 * (sd + refsd));
}

#endif
void createtest()
{
  int n, j, k;
  double start, end;
  double meantime, sd, hm;
  
  n = IDA;
  
  
  


	ipmacc_prompt((char*)"IPMACC: memory allocation btest\n");
acc_create((void*)btest,IDA*sizeof(double));
	

{


  
		for(k = 0; k <= OUTERREPS; k++)
 {
    
    gettimeofday(&tim, NULL);
    start = tim.tv_sec * 1000000.0 + tim.tv_usec;
    
    


			ipmacc_prompt((char*)"IPMACC: memory allocation btest\n");
acc_create((void*)btest,IDA*sizeof(double));
			

{


    int i;
}
			


    
    
    
    
    
    
    
    
    

    gettimeofday(&tim, NULL);
    end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
    times [k] = (end - start);
  }


}
	




  

  stats(&meantime, &sd, &hm);
  
  printf("%d: CREATETEST time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95 * sd);
  
}

void kerneltest()
{
  int n, j, k;
  double start, end;
  double meantime, sd, hm;
  
  n = IDA;
  printf("\n");
  
  

  int *arg1 = (int*)malloc(sizeof(int) * 64);
  int *arg2 = (int*)malloc(sizeof(int) * 64);
  int *arg3 = (int*)malloc(sizeof(int) * 64);
  int *arg4 = (int*)malloc(sizeof(int) * 64);
  int *arg5 = (int*)malloc(sizeof(int) * 64);
  int *arg6 = (int*)malloc(sizeof(int) * 64);
  int *arg7 = (int*)malloc(sizeof(int) * 64);
  int *arg8 = (int*)malloc(sizeof(int) * 64);
  int *arg9 = (int*)malloc(sizeof(int) * 64);
  int *arg10 = (int*)malloc(sizeof(int) * 64);
  int *arg11 = (int*)malloc(sizeof(int) * 64);
  int *arg12 = (int*)malloc(sizeof(int) * 64);
  int *arg13 = (int*)malloc(sizeof(int) * 64);
  int *arg14 = (int*)malloc(sizeof(int) * 64);
  int *arg15 = (int*)malloc(sizeof(int) * 64);
  int *arg16 = (int*)malloc(sizeof(int) * 64);


	ipmacc_prompt((char*)"IPMACC: memory allocation arg1\n");
acc_create((void*)arg1,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg2\n");
acc_create((void*)arg2,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg3\n");
acc_create((void*)arg3,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg4\n");
acc_create((void*)arg4,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg5\n");
acc_create((void*)arg5,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg6\n");
acc_create((void*)arg6,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg7\n");
acc_create((void*)arg7,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg8\n");
acc_create((void*)arg8,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg9\n");
acc_create((void*)arg9,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg10\n");
acc_create((void*)arg10,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg11\n");
acc_create((void*)arg11,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg12\n");
acc_create((void*)arg12,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg13\n");
acc_create((void*)arg13,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg14\n");
acc_create((void*)arg14,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg15\n");
acc_create((void*)arg15,(64+0)*sizeof(int));
ipmacc_prompt((char*)"IPMACC: memory allocation arg16\n");
acc_create((void*)arg16,(64+0)*sizeof(int));
	

{



  {
    
    
		for(k = 0; k <= OUTERREPS; k++)
 {
      gettimeofday(&tim, NULL);
      start = tim.tv_sec * 1000000.0 + tim.tv_usec;



						ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg1\n");
acc_present((void*)arg1);

/* kernel call statement*/
static cl_kernel __ipmacc_clkern0=NULL;
if( __ipmacc_clkern0==NULL){
const char* kernelSource0 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_0(__global int* arg1){\nint __kernel_getuid=get_global_id(0);\n{\n{\n{\nint i=0+(__kernel_getuid);\nif( i < 1)\n{\n        arg1 [i] = i;\n      }\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm0;
__ipmacc_clpgm0=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource0, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags0[128];
sprintf(__ipmacc_clcompileflags0, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm0, 0, NULL, __ipmacc_clcompileflags0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm0, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm0, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
__ipmacc_clkern0 = clCreateKernel(__ipmacc_clpgm0, "__generated_kernel_region_0", &__ipmacc_clerr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg1);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern0, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",((((abs((int)((1))-0))/(1))/256)+1)*256,256);
size_t global_item_size0 = ((((abs((int)((1))-0))/(1))/256)+1)*256;
size_t local_item_size0 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern0, 1, NULL,
 &global_item_size0, &local_item_size0, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);



      gettimeofday(&tim, NULL);
      end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
      times [k] = (end - start);
    }


    stats(&meantime, &sd, &hm);
    printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 1, hm, CONF95 * sd);

    
    
		for(k = 0; k <= OUTERREPS; k++)
 {
      gettimeofday(&tim, NULL);
      start = tim.tv_sec * 1000000.0 + tim.tv_usec;



						ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg1\n");
acc_present((void*)arg1);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg2\n");
acc_present((void*)arg2);

/* kernel call statement*/
static cl_kernel __ipmacc_clkern1=NULL;
if( __ipmacc_clkern1==NULL){
const char* kernelSource1 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_1(__global int* arg2,__global int* arg1){\nint __kernel_getuid=get_global_id(0);\n{\n{\n{\nint i=0+(__kernel_getuid);\nif( i < 1)\n{\n        arg1 [i] = i;\n        arg2 [i] = i;\n      }\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm1;
__ipmacc_clpgm1=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource1, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags1[128];
sprintf(__ipmacc_clcompileflags1, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm1, 0, NULL, __ipmacc_clcompileflags1, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm1, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm1, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
__ipmacc_clkern1 = clCreateKernel(__ipmacc_clpgm1, "__generated_kernel_region_1", &__ipmacc_clerr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg2);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern1, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg1);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern1, 1, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 1 > gridDim: %d\tblockDim: %d\n",((((abs((int)((1))-0))/(1))/256)+1)*256,256);
size_t global_item_size1 = ((((abs((int)((1))-0))/(1))/256)+1)*256;
size_t local_item_size1 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern1, 1, NULL,
 &global_item_size1, &local_item_size1, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);



      gettimeofday(&tim, NULL);
      end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
      times [k] = (end - start);
    }


    stats(&meantime, &sd, &hm);
    printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 2, hm, CONF95 * sd);

    
    
		for(k = 0; k <= OUTERREPS; k++)
 {
      gettimeofday(&tim, NULL);
      start = tim.tv_sec * 1000000.0 + tim.tv_usec;



						ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg1\n");
acc_present((void*)arg1);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg2\n");
acc_present((void*)arg2);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg3\n");
acc_present((void*)arg3);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg4\n");
acc_present((void*)arg4);

/* kernel call statement*/
static cl_kernel __ipmacc_clkern2=NULL;
if( __ipmacc_clkern2==NULL){
const char* kernelSource2 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_2(__global int* arg1,__global int* arg2,__global int* arg3,__global int* arg4){\nint __kernel_getuid=get_global_id(0);\n{\n{\n{\nint i=0+(__kernel_getuid);\nif( i < 1)\n{\n        arg1 [i] = i;\n        arg2 [i] = i;\n        arg3 [i] = i;\n        arg4 [i] = i;\n      }\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm2;
__ipmacc_clpgm2=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource2, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags2[128];
sprintf(__ipmacc_clcompileflags2, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm2, 0, NULL, __ipmacc_clcompileflags2, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm2, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm2, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
__ipmacc_clkern2 = clCreateKernel(__ipmacc_clpgm2, "__generated_kernel_region_2", &__ipmacc_clerr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg1);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg2);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 1, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg3);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 2, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg4);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern2, 3, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 2 > gridDim: %d\tblockDim: %d\n",((((abs((int)((1))-0))/(1))/256)+1)*256,256);
size_t global_item_size2 = ((((abs((int)((1))-0))/(1))/256)+1)*256;
size_t local_item_size2 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern2, 1, NULL,
 &global_item_size2, &local_item_size2, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);



      gettimeofday(&tim, NULL);
      end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
      times [k] = (end - start);
    }


    stats(&meantime, &sd, &hm);
    printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 4, hm, CONF95 * sd);

    
    
		for(k = 0; k <= OUTERREPS; k++)
 {
      gettimeofday(&tim, NULL);
      start = tim.tv_sec * 1000000.0 + tim.tv_usec;



						ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg1\n");
acc_present((void*)arg1);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg2\n");
acc_present((void*)arg2);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg3\n");
acc_present((void*)arg3);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg4\n");
acc_present((void*)arg4);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg5\n");
acc_present((void*)arg5);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg6\n");
acc_present((void*)arg6);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg7\n");
acc_present((void*)arg7);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg8\n");
acc_present((void*)arg8);

/* kernel call statement*/
static cl_kernel __ipmacc_clkern3=NULL;
if( __ipmacc_clkern3==NULL){
const char* kernelSource3 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_3(__global int* arg8,__global int* arg1,__global int* arg2,__global int* arg3,__global int* arg4,__global int* arg6,__global int* arg5,__global int* arg7){\nint __kernel_getuid=get_global_id(0);\n{\n{\n{\nint i=0+(__kernel_getuid);\nif( i < 1)\n{\n        arg1 [i] = i;\n        arg2 [i] = i;\n        arg3 [i] = i;\n        arg4 [i] = i;\n        arg5 [i] = i;\n        arg6 [i] = i;\n        arg7 [i] = i;\n        arg8 [i] = i;\n      }\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm3;
__ipmacc_clpgm3=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource3, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags3[128];
sprintf(__ipmacc_clcompileflags3, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm3, 0, NULL, __ipmacc_clcompileflags3, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm3, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm3, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
__ipmacc_clkern3 = clCreateKernel(__ipmacc_clpgm3, "__generated_kernel_region_3", &__ipmacc_clerr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg8);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg1);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 1, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg2);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 2, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg3);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 3, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg4);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 4, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg6);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 5, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg5);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 6, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg7);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern3, 7, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 3 > gridDim: %d\tblockDim: %d\n",((((abs((int)((1))-0))/(1))/256)+1)*256,256);
size_t global_item_size3 = ((((abs((int)((1))-0))/(1))/256)+1)*256;
size_t local_item_size3 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern3, 1, NULL,
 &global_item_size3, &local_item_size3, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);



      gettimeofday(&tim, NULL);
      end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
      times [k] = (end - start);
    }


    stats(&meantime, &sd, &hm);
    printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 8, hm, CONF95 * sd);

    
    
		for(k = 0; k <= OUTERREPS; k++)
 {
      gettimeofday(&tim, NULL);
      start = tim.tv_sec * 1000000.0 + tim.tv_usec;



						ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg1\n");
acc_present((void*)arg1);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg2\n");
acc_present((void*)arg2);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg3\n");
acc_present((void*)arg3);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg4\n");
acc_present((void*)arg4);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg5\n");
acc_present((void*)arg5);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg6\n");
acc_present((void*)arg6);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg7\n");
acc_present((void*)arg7);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg8\n");
acc_present((void*)arg8);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg9\n");
acc_present((void*)arg9);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg10\n");
acc_present((void*)arg10);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg11\n");
acc_present((void*)arg11);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg12\n");
acc_present((void*)arg12);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg13\n");
acc_present((void*)arg13);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg14\n");
acc_present((void*)arg14);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg15\n");
acc_present((void*)arg15);
ipmacc_prompt((char*)"IPMACC: memory getting device pointer for arg16\n");
acc_present((void*)arg16);

/* kernel call statement*/
static cl_kernel __ipmacc_clkern4=NULL;
if( __ipmacc_clkern4==NULL){
const char* kernelSource4 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_4(__global int* arg8,__global int* arg9,__global int* arg13,__global int* arg1,__global int* arg2,__global int* arg3,__global int* arg4,__global int* arg6,__global int* arg5,__global int* arg12,__global int* arg10,__global int* arg11,__global int* arg16,__global int* arg14,__global int* arg15,__global int* arg7){\nint __kernel_getuid=get_global_id(0);\n{\n{\n{\nint i=0+(__kernel_getuid);\nif( i < 1)\n{\n        arg1 [i] = i;\n        arg2 [i] = i;\n        arg3 [i] = i;\n        arg4 [i] = i;\n        arg5 [i] = i;\n        arg6 [i] = i;\n        arg7 [i] = i;\n        arg8 [i] = i;\n        arg9 [i] = i;\n        arg10 [i] = i;\n        arg11 [i] = i;\n        arg12 [i] = i;\n        arg13 [i] = i;\n        arg14 [i] = i;\n        arg15 [i] = i;\n        arg16 [i] = i;\n      }\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm4;
__ipmacc_clpgm4=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource4, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags4[128];
sprintf(__ipmacc_clcompileflags4, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm4, 0, NULL, __ipmacc_clcompileflags4, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm4, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm4, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
__ipmacc_clkern4 = clCreateKernel(__ipmacc_clpgm4, "__generated_kernel_region_4", &__ipmacc_clerr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg8);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg9);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 1, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg13);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 2, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg1);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 3, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg2);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 4, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg3);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 5, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg4);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 6, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg6);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 7, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg5);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 8, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg12);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 9, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg10);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 10, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg11);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 11, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg16);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 12, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg14);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 13, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg15);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 14, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(arg7);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern4, 15, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 4 > gridDim: %d\tblockDim: %d\n",((((abs((int)((1))-0))/(1))/256)+1)*256,256);
size_t global_item_size4 = ((((abs((int)((1))-0))/(1))/256)+1)*256;
size_t local_item_size4 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern4, 1, NULL,
 &global_item_size4, &local_item_size4, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);



      gettimeofday(&tim, NULL);
      end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
      times [k] = (end - start);
    }


    stats(&meantime, &sd, &hm);
    printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 16, hm, CONF95 * sd);
  }
}
	


}

void copyintest()
{
  int n, j, k;
  double start, end;
  double meantime, sd, hm;
  
  n = IDA;
  
  
  


	ipmacc_prompt((char*)"IPMACC: memory allocation btest\n");
acc_create((void*)btest,IDA*sizeof(double));
	

{


  
		for(k = 0; k <= OUTERREPS; k++)
 {
    
    gettimeofday(&tim, NULL);
    start = tim.tv_sec * 1000000.0 + tim.tv_usec;
    
    



			ipmacc_prompt((char*)"IPMACC: memory allocation btest\n");
acc_present_or_create((void*)btest,IDA*sizeof(double));
			ipmacc_prompt((char*)"IPMACC: memory copyin btest\n");
acc_pcopyin((void*)btest,IDA*sizeof(double));


{


    int i;
}
			


    
    
    
    
    
    
    

    gettimeofday(&tim, NULL);
    end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
    times [k] = (end - start);
  }


}
	




  

  stats(&meantime, &sd, &hm);
  
  printf("%d: COPYIN time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95 * sd);
  
}

void copyouttest()
{
  int n, j, k;
  double start, end;
  double meantime, sd, hm;
  
  n = IDA;
  
  
  


	ipmacc_prompt((char*)"IPMACC: memory allocation btest\n");
acc_create((void*)btest,IDA*sizeof(double));
	

{


  
		for(k = 0; k <= OUTERREPS; k++)
 {
    
    gettimeofday(&tim, NULL);
    start = tim.tv_sec * 1000000.0 + tim.tv_usec;
    
    



			ipmacc_prompt((char*)"IPMACC: memory allocation btest\n");
acc_present_or_create((void*)btest,IDA*sizeof(double));
			

{


    int i;
}
			ipmacc_prompt((char*)"IPMACC: memory copyout btest\n");
acc_copyout_and_keep((void*)btest,IDA*sizeof(double));



    
    
    
    
    
    
    

    gettimeofday(&tim, NULL);
    end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
    times [k] = (end - start);
  }


}
	




  

  stats(&meantime, &sd, &hm);
  
  printf("%d: COPYOUT time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95 * sd);

  
}

void reductiontest()
{
  int n, j, k;
  double start, end;
  double meantime, sd, hm;
  double result = 0;
  
  n = IDA;
  printf("\n");
  
  
  

	ipmacc_prompt((char*)"IPMACC: memory allocation btest\n");
acc_create((void*)btest,IDA*sizeof(double));
	ipmacc_prompt((char*)"IPMACC: memory copyin btest\n");
acc_copyin((void*)btest,IDA*sizeof(double));


{


  {
    
    
		for(k = 0; k <= OUTERREPS; k++)
 {
      gettimeofday(&tim, NULL);
      start = tim.tv_sec * 1000000.0 + tim.tv_usec;

      

ipmacc_prompt((char*)"IPMACC: memory allocation result\n");
double* __ipmacc_reduction_array_result=NULL;
if(__ipmacc_reduction_array_result==NULL){
__ipmacc_reduction_array_result=(double*)malloc((((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));
acc_create((void*)__ipmacc_reduction_array_result,(((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));
for(int __ipmacc_initialize_rv=0; __ipmacc_initialize_rv<(((abs((int)((IDA))-0))/(1))/256+1); __ipmacc_initialize_rv++){
__ipmacc_reduction_array_result[__ipmacc_initialize_rv]= 0;
}
acc_pcopyin((void*)__ipmacc_reduction_array_result,(((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));
}

/* kernel call statement*/
static cl_kernel __ipmacc_clkern5=NULL;
if( __ipmacc_clkern5==NULL){
const char* kernelSource5 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_5(__global double* btest,__global double* result__ipmacc_reductionarray_internal){\nint __kernel_getuid=get_global_id(0);\n__local double __kernel_reduction_shmem_double[256];\nint j;\nint __kernel_reduction_iterator=0;\ndouble result;{\n{\n{\n j=0+(__kernel_getuid);\nif( j < 4782969)\n{\n\n{\ndouble result=0;\n\n{\n        double x = btest [j];\n        result += x;\n      }\n\n\n\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n__kernel_reduction_shmem_double[get_local_id(0)]=result;\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\nfor(__kernel_reduction_iterator=256/2;__kernel_reduction_iterator>0; __kernel_reduction_iterator>>=1) {\nif(get_local_id(0)<__kernel_reduction_iterator){\n__kernel_reduction_shmem_double[get_local_id(0)]=__kernel_reduction_shmem_double[get_local_id(0)]+__kernel_reduction_shmem_double[get_local_id(0)+__kernel_reduction_iterator];\n}\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n}\n}\nif(get_local_id(0)==0){\nresult__ipmacc_reductionarray_internal[get_group_id(0)]=__kernel_reduction_shmem_double[0];\n}\n\n}\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm5;
__ipmacc_clpgm5=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource5, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags5[128];
sprintf(__ipmacc_clcompileflags5, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm5, 0, NULL, __ipmacc_clcompileflags5, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm5, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm5, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
__ipmacc_clkern5 = clCreateKernel(__ipmacc_clpgm5, "__generated_kernel_region_5", &__ipmacc_clerr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(btest);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern5, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(__ipmacc_reduction_array_result);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern5, 1, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 5 > gridDim: %d\tblockDim: %d\n",((((abs((int)((IDA))-0))/(1))/256)+1)*256,256);
size_t global_item_size5 = ((((abs((int)((IDA))-0))/(1))/256)+1)*256;
size_t local_item_size5 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern5, 1, NULL,
 &global_item_size5, &local_item_size5, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
ipmacc_prompt((char*)"IPMACC: memory copyout result\n");
acc_copyout_and_keep((void*)__ipmacc_reduction_array_result,(((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));

/* second-level reduction on result */
{
int __kernel_reduction_iterator=0;
{
int bound = (((abs((int)((IDA))-0))/(1))/256+1)-1;
for(__kernel_reduction_iterator=bound; __kernel_reduction_iterator>0; __kernel_reduction_iterator-=1){
__ipmacc_reduction_array_result[__kernel_reduction_iterator-1]=__ipmacc_reduction_array_result[__kernel_reduction_iterator-1]+__ipmacc_reduction_array_result[__kernel_reduction_iterator];
}
}
}
result=__ipmacc_reduction_array_result[0];
free(__ipmacc_reduction_array_result);
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);




      gettimeofday(&tim, NULL);
      end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
      times [k] = (end - start);
    }


    stats(&meantime, &sd, &hm);
    printf("%d: REDUCTION(+) time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95 * sd);

    
    
		for(k = 0; k <= OUTERREPS; k++)
 {
      gettimeofday(&tim, NULL);
      start = tim.tv_sec * 1000000.0 + tim.tv_usec;

      

ipmacc_prompt((char*)"IPMACC: memory allocation result\n");
double* __ipmacc_reduction_array_result=NULL;
if(__ipmacc_reduction_array_result==NULL){
__ipmacc_reduction_array_result=(double*)malloc((((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));
acc_create((void*)__ipmacc_reduction_array_result,(((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));
for(int __ipmacc_initialize_rv=0; __ipmacc_initialize_rv<(((abs((int)((IDA))-0))/(1))/256+1); __ipmacc_initialize_rv++){
__ipmacc_reduction_array_result[__ipmacc_initialize_rv]= INT_MAX;
}
acc_pcopyin((void*)__ipmacc_reduction_array_result,(((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));
}

/* kernel call statement*/
static cl_kernel __ipmacc_clkern6=NULL;
if( __ipmacc_clkern6==NULL){
const char* kernelSource6 ="#ifdef cl_khr_fp64\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\n#elif defined(cl_amd_fp64)\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\n#else\n#error \"Double precision floating point not supported by OpenCL implementation.\"\n#endif\n\n\n\n__kernel void __generated_kernel_region_6(__global double* btest,__global double* result__ipmacc_reductionarray_internal){\nint __kernel_getuid=get_global_id(0);\n__local double __kernel_reduction_shmem_double[256];\nint j;\nint __kernel_reduction_iterator=0;\ndouble result;{\n{\n{\n j=0+(__kernel_getuid);\nif( j < 4782969)\n{\n\n{\ndouble result=0;\n\n{\n        double x = btest [j];\n        result += x;\n      }\n\n\n\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n__kernel_reduction_shmem_double[get_local_id(0)]=result;\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\nfor(__kernel_reduction_iterator=256/2;__kernel_reduction_iterator>0; __kernel_reduction_iterator>>=1) {\nif(get_local_id(0)<__kernel_reduction_iterator){\n__kernel_reduction_shmem_double[get_local_id(0)]=(__kernel_reduction_shmem_double[get_local_id(0)]>__kernel_reduction_shmem_double[get_local_id(0)+__kernel_reduction_iterator]?__kernel_reduction_shmem_double[get_local_id(0)]:__kernel_reduction_shmem_double[get_local_id(0)+__kernel_reduction_iterator]);\n}\nbarrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n}\n}\nif(get_local_id(0)==0){\nresult__ipmacc_reductionarray_internal[get_group_id(0)]=__kernel_reduction_shmem_double[0];\n}\n\n}\n\n}\n}\n}\n}";
cl_program __ipmacc_clpgm6;
__ipmacc_clpgm6=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource6, NULL, &__ipmacc_clerr);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
exit(-1);
}
char __ipmacc_clcompileflags6[128];
sprintf(__ipmacc_clcompileflags6, " ");
__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm6, 0, NULL, __ipmacc_clcompileflags6, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm6, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm6, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d)---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);exit(-1);
}
__ipmacc_clkern6 = clCreateKernel(__ipmacc_clpgm6, "__generated_kernel_region_6", &__ipmacc_clerr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(btest);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern6, 0, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
{
cl_mem ptr=(cl_mem)acc_deviceptr(__ipmacc_reduction_array_result);
__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern6, 1, sizeof(cl_mem), (void *)&ptr);
}
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
exit(-1);
}
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 6 > gridDim: %d\tblockDim: %d\n",((((abs((int)((IDA))-0))/(1))/256)+1)*256,256);
size_t global_item_size6 = ((((abs((int)((IDA))-0))/(1))/256)+1)*256;
size_t local_item_size6 = 256;
__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern6, 1, NULL,
 &global_item_size6, &local_item_size6, 0, NULL, NULL);
if(__ipmacc_clerr!=CL_SUCCESS){
printf("OpenCL Runtime Error in clEnqueueNDRangeKernel! id: %d\n",__ipmacc_clerr);
exit(-1);
}

/* kernel call statement*/
ipmacc_prompt((char*)"IPMACC: memory copyout result\n");
acc_copyout_and_keep((void*)__ipmacc_reduction_array_result,(((abs((int)((IDA))-0))/(1))/256+1)*sizeof(double));

/* second-level reduction on result */
{
int __kernel_reduction_iterator=0;
{
int bound = (((abs((int)((IDA))-0))/(1))/256+1)-1;
for(__kernel_reduction_iterator=bound; __kernel_reduction_iterator>0; __kernel_reduction_iterator-=1){
__ipmacc_reduction_array_result[__kernel_reduction_iterator-1]=(__ipmacc_reduction_array_result[__kernel_reduction_iterator-1]>__ipmacc_reduction_array_result[__kernel_reduction_iterator]?__ipmacc_reduction_array_result[__kernel_reduction_iterator-1]:__ipmacc_reduction_array_result[__kernel_reduction_iterator]);
}
}
}
result=__ipmacc_reduction_array_result[0];
free(__ipmacc_reduction_array_result);
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
clFlush(__ipmacc_command_queue);




      gettimeofday(&tim, NULL);
      end = tim.tv_sec * 1000000.0 + (tim.tv_usec);
      times [k] = (end - start);
    }


    stats(&meantime, &sd, &hm);
    printf("%d: REDUCTION(max) time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95 * sd);
  }
}
	


  reftime = meantime;
  refsd = sd;
}

void privatetest()
{
  int j, k;
  int i = 0;
  double start;
  double meantime, sd;
  
  double a;
  

  printf("\n");
  printf("--------------------------------------------------------\n");
  printf("Computing REDUCTION time 1\n");

  for (k = 0; k <= OUTERREPS; k++) {
    start = getclock();
    
    
    for (j = 0; j < innerreps; j++) {
      delay(delaylength, &a);
      i++;
    }
    times [k] = (getclock() - start) * 1.0e6 / (double)innerreps;
  }

  

  printf("PRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95 * sd);
  printf("PRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime - reftime, CONF95 * (sd + refsd));

  reftime = meantime;
  refsd = sd;
}

void stats(double *mtp, double *sdp, double *hm)
{
  double meantime, totaltime, sumsq, mintime, maxtime, sd, cutoff;
  double reciprocal, harmonic_mean;
  int i, nr;

  mintime = 1.0e10;
  maxtime = 0.;
  totaltime = 0.;

  for (i = 1; i <= OUTERREPS; i++) {
    mintime = (mintime < times [i]) ? mintime : times [i];
    maxtime = (maxtime > times [i]) ? maxtime : times [i];
    totaltime += times [i];
    reciprocal += 1 / times [i];
  }

  meantime = totaltime / OUTERREPS;
  harmonic_mean = OUTERREPS / reciprocal;
  sumsq = 0;

  for (i = 1; i <= OUTERREPS; i++) {
    sumsq += (times [i] - meantime) * (times [i] - meantime);
  }
  sd = sqrt(sumsq / (OUTERREPS - 1));

  cutoff = 3.0 * sd;

  nr = 0;

  for (i = 1; i <= OUTERREPS; i++) {
    if (fabs(times [i] - meantime) > cutoff) {
      nr++;
    }
  }

  
  
  
  

  *mtp = meantime;
  *sdp = sd;
  *hm = harmonic_mean;
}



