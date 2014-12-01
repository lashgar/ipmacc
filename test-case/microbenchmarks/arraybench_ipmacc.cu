#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#include <cuda.h>






















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

  __global__ void __generated_kernel_region_0(int* arg1);
 
  __global__ void __generated_kernel_region_1(int* arg2,int* arg1);
 
  __global__ void __generated_kernel_region_2(int* arg1,int* arg2,int* arg3,int* arg4);
 
  __global__ void __generated_kernel_region_3(int* arg8,int* arg1,int* arg2,int* arg3,int* arg4,int* arg6,int* arg5,int* arg7);
 
  __global__ void __generated_kernel_region_4(int* arg8,int* arg9,int* arg13,int* arg1,int* arg2,int* arg3,int* arg4,int* arg6,int* arg5,int* arg12,int* arg10,int* arg11,int* arg16,int* arg14,int* arg15,int* arg7);
 
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

/* kernel call statement [2, 3]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",(((abs((int)((1))-0))/(1)))/256+1,256);
__generated_kernel_region_0<<<(((abs((int)((1))-0))/(1)))/256+1,256>>>(
(int*)acc_deviceptr((void*)arg1));
/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
cudaDeviceSynchronize();



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

/* kernel call statement [2, 4]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 1 > gridDim: %d\tblockDim: %d\n",(((abs((int)((1))-0))/(1)))/256+1,256);
__generated_kernel_region_1<<<(((abs((int)((1))-0))/(1)))/256+1,256>>>(
(int*)acc_deviceptr((void*)arg2),
(int*)acc_deviceptr((void*)arg1));
/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
cudaDeviceSynchronize();



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

/* kernel call statement [2, 5]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 2 > gridDim: %d\tblockDim: %d\n",(((abs((int)((1))-0))/(1)))/256+1,256);
__generated_kernel_region_2<<<(((abs((int)((1))-0))/(1)))/256+1,256>>>(
(int*)acc_deviceptr((void*)arg1),
(int*)acc_deviceptr((void*)arg2),
(int*)acc_deviceptr((void*)arg3),
(int*)acc_deviceptr((void*)arg4));
/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
cudaDeviceSynchronize();



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

/* kernel call statement [2, 6]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 3 > gridDim: %d\tblockDim: %d\n",(((abs((int)((1))-0))/(1)))/256+1,256);
__generated_kernel_region_3<<<(((abs((int)((1))-0))/(1)))/256+1,256>>>(
(int*)acc_deviceptr((void*)arg8),
(int*)acc_deviceptr((void*)arg1),
(int*)acc_deviceptr((void*)arg2),
(int*)acc_deviceptr((void*)arg3),
(int*)acc_deviceptr((void*)arg4),
(int*)acc_deviceptr((void*)arg6),
(int*)acc_deviceptr((void*)arg5),
(int*)acc_deviceptr((void*)arg7));
/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
cudaDeviceSynchronize();



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

/* kernel call statement [2, 7]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 4 > gridDim: %d\tblockDim: %d\n",(((abs((int)((1))-0))/(1)))/256+1,256);
__generated_kernel_region_4<<<(((abs((int)((1))-0))/(1)))/256+1,256>>>(
(int*)acc_deviceptr((void*)arg8),
(int*)acc_deviceptr((void*)arg9),
(int*)acc_deviceptr((void*)arg13),
(int*)acc_deviceptr((void*)arg1),
(int*)acc_deviceptr((void*)arg2),
(int*)acc_deviceptr((void*)arg3),
(int*)acc_deviceptr((void*)arg4),
(int*)acc_deviceptr((void*)arg6),
(int*)acc_deviceptr((void*)arg5),
(int*)acc_deviceptr((void*)arg12),
(int*)acc_deviceptr((void*)arg10),
(int*)acc_deviceptr((void*)arg11),
(int*)acc_deviceptr((void*)arg16),
(int*)acc_deviceptr((void*)arg14),
(int*)acc_deviceptr((void*)arg15),
(int*)acc_deviceptr((void*)arg7));
/* kernel call statement*/
			if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
cudaDeviceSynchronize();



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

  __global__ void __generated_kernel_region_5(double* btest,double* result__ipmacc_reductionarray_internal);
 
  __global__ void __generated_kernel_region_6(double* btest,double* result__ipmacc_reductionarray_internal);
 
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

/* kernel call statement [-1, 12]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 5 > gridDim: %d\tblockDim: %d\n",(((abs((int)((IDA))-0))/(1)))/256+1,256);
__generated_kernel_region_5<<<(((abs((int)((IDA))-0))/(1)))/256+1,256>>>(
(double*)acc_deviceptr((void*)btest),
(double*)acc_deviceptr((void*)__ipmacc_reduction_array_result));
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
cudaDeviceSynchronize();




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

/* kernel call statement [-1, 12]*/
if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 6 > gridDim: %d\tblockDim: %d\n",(((abs((int)((IDA))-0))/(1)))/256+1,256);
__generated_kernel_region_6<<<(((abs((int)((IDA))-0))/(1)))/256+1,256>>>(
(double*)acc_deviceptr((void*)btest),
(double*)acc_deviceptr((void*)__ipmacc_reduction_array_result));
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
cudaDeviceSynchronize();




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


 __global__ void __generated_kernel_region_0(int* arg1){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
{
{
{
int i=0+(__kernel_getuid);
if( i < 1)
{
        arg1 [i] = i;
      }

}
}
}
}
 __global__ void __generated_kernel_region_1(int* arg2,int* arg1){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
{
{
{
int i=0+(__kernel_getuid);
if( i < 1)
{
        arg1 [i] = i;
        arg2 [i] = i;
      }

}
}
}
}
 __global__ void __generated_kernel_region_2(int* arg1,int* arg2,int* arg3,int* arg4){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
{
{
{
int i=0+(__kernel_getuid);
if( i < 1)
{
        arg1 [i] = i;
        arg2 [i] = i;
        arg3 [i] = i;
        arg4 [i] = i;
      }

}
}
}
}
 __global__ void __generated_kernel_region_3(int* arg8,int* arg1,int* arg2,int* arg3,int* arg4,int* arg6,int* arg5,int* arg7){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
{
{
{
int i=0+(__kernel_getuid);
if( i < 1)
{
        arg1 [i] = i;
        arg2 [i] = i;
        arg3 [i] = i;
        arg4 [i] = i;
        arg5 [i] = i;
        arg6 [i] = i;
        arg7 [i] = i;
        arg8 [i] = i;
      }

}
}
}
}
 __global__ void __generated_kernel_region_4(int* arg8,int* arg9,int* arg13,int* arg1,int* arg2,int* arg3,int* arg4,int* arg6,int* arg5,int* arg12,int* arg10,int* arg11,int* arg16,int* arg14,int* arg15,int* arg7){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
{
{
{
int i=0+(__kernel_getuid);
if( i < 1)
{
        arg1 [i] = i;
        arg2 [i] = i;
        arg3 [i] = i;
        arg4 [i] = i;
        arg5 [i] = i;
        arg6 [i] = i;
        arg7 [i] = i;
        arg8 [i] = i;
        arg9 [i] = i;
        arg10 [i] = i;
        arg11 [i] = i;
        arg12 [i] = i;
        arg13 [i] = i;
        arg14 [i] = i;
        arg15 [i] = i;
        arg16 [i] = i;
      }

}
}
}
}
 __global__ void __generated_kernel_region_5(double* btest,double* result__ipmacc_reductionarray_internal){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
__shared__ double __kernel_reduction_shmem_double[256];
int j;
int __kernel_reduction_iterator=0;
double result;{
{
{
 j=0+(__kernel_getuid);
if( j < IDA)
{ //opened for private and reduction
/*private:+:result*/
{ //start of reduction region for result 
double result=0;

{
        double x = btest [j];
        result += x;
      }
/*reduction:+:result*/

/* reduction on result */
__syncthreads();
__kernel_reduction_shmem_double[threadIdx.x]=result;
__syncthreads();
for(__kernel_reduction_iterator=blockDim.x/2;__kernel_reduction_iterator>0; __kernel_reduction_iterator>>=1) {
if(threadIdx.x<__kernel_reduction_iterator){
__kernel_reduction_shmem_double[threadIdx.x]=__kernel_reduction_shmem_double[threadIdx.x]+__kernel_reduction_shmem_double[threadIdx.x+__kernel_reduction_iterator];
}
__syncthreads();
}
}// the end of result scope
if(threadIdx.x==0){
result__ipmacc_reductionarray_internal[blockIdx.x]=__kernel_reduction_shmem_double[0];
}

} // closed for reduction-end

}
}
}
}
 __global__ void __generated_kernel_region_6(double* btest,double* result__ipmacc_reductionarray_internal){
int __kernel_getuid=threadIdx.x+blockIdx.x*blockDim.x;
__shared__ double __kernel_reduction_shmem_double[256];
int j;
int __kernel_reduction_iterator=0;
double result;{
{
{
 j=0+(__kernel_getuid);
if( j < IDA)
{ //opened for private and reduction
/*private:max:result*/
{ //start of reduction region for result 
double result=0;

{
        double x = btest [j];
        result += x;
      }
/*reduction:max:result*/

/* reduction on result */
__syncthreads();
__kernel_reduction_shmem_double[threadIdx.x]=result;
__syncthreads();
for(__kernel_reduction_iterator=blockDim.x/2;__kernel_reduction_iterator>0; __kernel_reduction_iterator>>=1) {
if(threadIdx.x<__kernel_reduction_iterator){
__kernel_reduction_shmem_double[threadIdx.x]=(__kernel_reduction_shmem_double[threadIdx.x]>__kernel_reduction_shmem_double[threadIdx.x+__kernel_reduction_iterator]?__kernel_reduction_shmem_double[threadIdx.x]:__kernel_reduction_shmem_double[threadIdx.x+__kernel_reduction_iterator]);
}
__syncthreads();
}
}// the end of result scope
if(threadIdx.x==0){
result__ipmacc_reductionarray_internal[blockIdx.x]=__kernel_reduction_shmem_double[0];
}

} // closed for reduction-end

}
}
}
}

