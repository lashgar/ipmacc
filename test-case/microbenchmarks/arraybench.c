/// ***************************************************************************
// *                                                                         *
// *             OpenMP MicroBenchmark Suite - Version 2.0                   *
// *                                                                         *
// *                            produced by                                  *
// *                                                                         *
// *                     Mark Bull and Fiona Reid                            *
// *                                                                         *
// *                                at                                       *
// *                                                                         *
// *                Edinburgh Parallel Computing Centre                      *
// *                                                                         *
// *         email: markb@epcc.ed.ac.uk or fiona@epcc.ed.ac.uk               *
// *                                                                         *
// *                                                                         *
// *      This version copyright (c) The University of Edinburgh, 2004.      *
// *                         All rights reserved.                            *
// *                                                                         *
// ***************************************************************************


#include <stdio.h> 
#include <stdlib.h>
#include <math.h> 
#define __STDC_LIMIT_MACROS
#include <stdint.h> //or <cstdint>
//#include <limits>
#include <climits>
#include "arraybench.h"
#include <sys/time.h>

double btest[IDA];
double atest[IDA];
int nthreads, delaylength, innerreps; 
double times[OUTERREPS+1], reftime, refsd; 

time_t starttime = 0; 
timeval tim;
//extern double getclock(void); 
//extern void delay(int, double*);

int main (int argv, char **argc)
{
#ifdef __NVCUDA__
	acc_init( acc_device_nvcuda );
#endif 
#ifdef __NVOPENCL__
	acc_init( acc_device_nvocl );
	//acc_list_devices_spec( acc_device_nvocl );
#endif 



	printf(" *******************************************************\n"); 

	delaylength = 500;
	innerreps = 100;
	// GENERATE REFERENCE TIME 
	//	refer();   

	// TEST  PRIVATE 
	//estprivnew(); 

	// TEST  FIRSTPRIVATE 
	//estfirstprivnew(); 

#ifdef OMPVER2
	// TEST  COPYPRIVATE / 
	//estcopyprivnew(); 
#endif

	//TEST  COPYIN 
	copyintest(); 

	//  TEST  COPYOUT 
	copyouttest();

	//  TEST  CREATE 
	createtest();


	// TEST  REDUCTION 
	reductiontest(); 

	// TEST  REDUCTION 
	kerneltest(); 


	// TEST  PRIVATE  
	//	privatetest(); 



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

	t = (double) (ts.tv_sec - starttime)  + (double) ts.tv_usec * 1.0e-6; 

	return t; 

}

void init_time_of_day_()
{
	struct  timeval  ts;
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
/*
   void delay(int delaylength)
   {

   int  i; 
   float a=0.; 

   for (i=0; i<delaylength; i++) a+=i; 
   if (a < 0) printf("%f \n",a); 

   } 
   */
void delay(int delaylength, double a[1])
{

	int  i; 
	a[0] = 1.0; 
	for (i=0; i<delaylength; i++) a[0]+=i; 
	// if (a[0] < 0) printf("%f \n",a); 

} 
void refer()
{
	int j,k;
	int i = 0 ; 
	double start; 
	double meantime, sd, hm; 
	double a[1];
	//  double getclock(void); 

	printf("\n");
	printf("--------------------------------------------------------\n");
	printf("Computing reference time 1\n"); 

	for (k=0; k<=OUTERREPS; k++){
		start  = getclock(); 
		for (j=0; j<innerreps; j++){
			delay(delaylength, a); 
			i++;	
		}
		times[k] = (getclock() - start) * 1.0e6 / (double) innerreps;
	}

	stats (&meantime, &sd, &hm);

	//	printf("Reference_time_1 =                        %10.3f microseconds +/- %10.3f\n", meantime, CONF95*sd);
	printf("Reference_time_1 =                        %10.3f microseconds +/- %10.3f\n", hm, CONF95*sd);

	reftime = meantime;
	refsd = sd;  
}

void testfirstprivnew()
{

	int n,j,k; 
	double start; 
	double meantime, sd; 
	//  double getclock(void); 

	n=IDA;
	printf("\n");
	printf("--------------------------------------------------------\n");
	printf("Computing FIRSTPRIVATE %d time\n", n); 

	for (k=0; k<=OUTERREPS; k++){
		start  = getclock(); 
		//	#pragma acc ker
		for (j=0; j<innerreps; j++){
			//#pragma omp parallel firstprivate(atest) 
			{
				delay(delaylength, atest); 
			}     
		}
		times[k] = (getclock() - start) * 1.0e6 / (double) innerreps;
	}

	//	stats (&meantime, &sd);

	//	stats (&meantime, &sd, &hm);
	printf("FIRSTPRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95*sd);  
	printf("FIRSTPRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime-reftime, CONF95*(sd+refsd));

}

void testprivnew()
{

	int n,j,k; 
	double start; 
	double meantime, sd; 
	// double getclock(void); 

	n=IDA;
	printf("\n");
	printf("--------------------------------------------------------\n");
	printf("Computing PRIVATE %d time\n", n); 

	for (k=0; k<=OUTERREPS; k++){
		start  = getclock(); 
		for (j=0; j<innerreps; j++){
			//#pragma omp parallel private(atest) 
			{
				delay(delaylength, atest); 
			}     
		}
		times[k] = (getclock() - start) * 1.0e6 / (double) innerreps;
	}

	//	stats (&meantime, &sd);

	//tats (&meantime, &sd, &hm);
	printf("PRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95*sd);  
	printf("PRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime-reftime, CONF95*(sd+refsd));

}

#ifdef OMPVER2
void testcopyprivnew()
{

	int n,j,k; 
	double start; 
	double meantime, sd; 
	//  double getclock(void); 
	n=IDA;
	printf("\n");
	printf("--------------------------------------------------------\n");
	printf("Computing COPYPRIVATE %d time\n", n); 

	for (k=0; k<=OUTERREPS; k++){
		start  = getclock(); 
		for (j=0; j<innerreps; j++){
			//#pragma omp single copyprivate(btest) 
			{
				delay(delaylength, btest); 
			}     
		}
		times[k] = (getclock() - start) * 1.0e6 / (double) innerreps;
	}

	//	stats (&meantime, &sd);

	printf("COPYPRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95*sd);
	printf("COPYPRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime-reftime, CONF95*(sd+refsd));

}
#endif
void createtest()
{

	int n,j,k; 
	double start,end;
	double meantime, sd, hm;
	//  double getclock(void); 
	n=IDA;
	//printf("\n");
	//	printf("--------------------------------------------------------\n");
	//	printf("Computing CREATETEST %d time\n", n); 
#pragma acc data create(btest[0:n])
	for (k=0; k<=OUTERREPS; k++){
		//	START  = GETCLOCK();
		gettimeofday(&tim, NULL);
		start=tim.tv_sec*1000000.0 + tim.tv_usec;
		//#PRAGMA ACC KERNELS COPYIN(BTEST[0:N]) 
		//#PRAGMA ACC LOOP INDEPENDENT 
#pragma acc data create(btest[0:n])
		int i;
		//#pragma acc data pcopyin(btest[0:n])
		//t i ;
		//ragma acc loop independent			
		//		for (j=0; j<innerreps; j++){
		//#PRAGMA OMP PARALLEL COPYIN(BTEST) 
		//			{
		//				delay(delaylength, btest); 
		//			}     
		//		}

		gettimeofday(&tim, NULL);
		end=tim.tv_sec*1000000.0 + (tim.tv_usec);
		times[k] = ( end - start ) ;
	}


	//	stats (&meantime, &sd);

	stats (&meantime, &sd, &hm);
	//	printf("%d: CREATETEST time =  %10.3f microseconds +/- %10.3f\n", n, meantime, CONF95*sd);
	printf("%d: CREATETEST time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95*sd);
	//	printf("CREATETEST overhead =                       %10.3f microseconds +/- %10.3f\n", meantime-reftime, CONF95*(sd+refsd));

}

void kerneltest()
{

	int n,j,k; 
	double start,end;
	double meantime, sd, hm;
	//  double getclock(void); 
	n=IDA;
	printf("\n");
	//	printf("--------------------------------------------------------\n");
	//	printf("Computing PRESENTTEST %d time\n", n); 

	int *arg1 =(int*)malloc(sizeof(int)*64);
	int *arg2 =(int*)malloc(sizeof(int)*64);
	int *arg3 =(int*)malloc(sizeof(int)*64);
	int *arg4 =(int*)malloc(sizeof(int)*64);
	int *arg5 =(int*)malloc(sizeof(int)*64);
	int *arg6 =(int*)malloc(sizeof(int)*64);
	int *arg7 =(int*)malloc(sizeof(int)*64);
	int *arg8 =(int*)malloc(sizeof(int)*64);
	int *arg9 =(int*)malloc(sizeof(int)*64);
	int *arg10=(int*)malloc(sizeof(int)*64);
	int *arg11=(int*)malloc(sizeof(int)*64);
	int *arg12=(int*)malloc(sizeof(int)*64);
	int *arg13=(int*)malloc(sizeof(int)*64);
	int *arg14=(int*)malloc(sizeof(int)*64);
	int *arg15=(int*)malloc(sizeof(int)*64);
	int *arg16=(int*)malloc(sizeof(int)*64);
#pragma acc data create(arg1[0:64],arg2 [0:64],arg3 [0:64],arg4 [0:64],arg5 [0:64],arg6 [0:64],arg7 [0:64],arg8 [0:64],arg9 [0:64],arg10[0:64],arg11[0:64],arg12[0:64],arg13[0:64],arg14[0:64],arg15[0:64],arg16[0:64])

	{
		// number of kernel args: 1
		for (k=0; k<=OUTERREPS; k++){
			gettimeofday(&tim, NULL);
			start=tim.tv_sec*1000000.0 + tim.tv_usec;

#pragma acc kernels present(arg1[0:64])
#pragma acc loop independent
			for(int i = 0 ; i < 1 ; i++) {
				arg1 [i]=i;
			}
			gettimeofday(&tim, NULL);
			end=tim.tv_sec*1000000.0 + (tim.tv_usec);
			times[k] = ( end - start ) ;
		}
		stats (&meantime, &sd, &hm);
		printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 1, hm, CONF95*sd);

		// number of kernel args: 2
		for (k=0; k<=OUTERREPS; k++){
			gettimeofday(&tim, NULL);
			start=tim.tv_sec*1000000.0 + tim.tv_usec;

#pragma acc kernels present(arg1[0:64],arg2[0:64])
#pragma acc loop independent
			for(int i = 0 ; i < 1 ; i++) {
				arg1 [i]=i;
				arg2 [i]=i;
			}
			gettimeofday(&tim, NULL);
			end=tim.tv_sec*1000000.0 + (tim.tv_usec);
			times[k] = ( end - start ) ;
		}
		stats (&meantime, &sd, &hm);
		printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 2, hm, CONF95*sd);

		// number of kernel args: 4
		for (k=0; k<=OUTERREPS; k++){
			gettimeofday(&tim, NULL);
			start=tim.tv_sec*1000000.0 + tim.tv_usec;

#pragma acc kernels present(arg1[0:64],arg2[0:64],arg3[0:64],arg4[0:64])
#pragma acc loop independent
			for(int i = 0 ; i < 1 ; i++) {
				arg1 [i]=i;
				arg2 [i]=i;
				arg3 [i]=i;
				arg4 [i]=i;
			}
			gettimeofday(&tim, NULL);
			end=tim.tv_sec*1000000.0 + (tim.tv_usec);
			times[k] = ( end - start ) ;
		}
		stats (&meantime, &sd, &hm);
		printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 4, hm, CONF95*sd);

		// number of kernel args: 8
		for (k=0; k<=OUTERREPS; k++){
			gettimeofday(&tim, NULL);
			start=tim.tv_sec*1000000.0 + tim.tv_usec;

#pragma acc kernels present(arg1[0:64],arg2[0:64],arg3[0:64],arg4[0:64],arg5[0:64],arg6[0:64],arg7[0:64],arg8[0:64])
#pragma acc loop independent
			for(int i = 0 ; i < 1 ; i++) {
				arg1 [i]=i;
				arg2 [i]=i;
				arg3 [i]=i;
				arg4 [i]=i;
				arg5 [i]=i;
				arg6 [i]=i;
				arg7 [i]=i;
				arg8 [i]=i;
			}
			gettimeofday(&tim, NULL);
			end=tim.tv_sec*1000000.0 + (tim.tv_usec);
			times[k] = ( end - start ) ;
		}
		stats (&meantime, &sd, &hm);
		printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 8, hm, CONF95*sd);

		// number of kernel args: 16
		for (k=0; k<=OUTERREPS; k++){
			gettimeofday(&tim, NULL);
			start=tim.tv_sec*1000000.0 + tim.tv_usec;

#pragma acc kernels present(arg1[0:64],arg2[0:64],arg3[0:64],arg4[0:64],arg5[0:64],arg6[0:64],arg7[0:64],arg8[0:64],arg9[0:64],arg10[0:64],arg11[0:64],arg12[0:64],arg13[0:64],arg14[0:64],arg15[0:64],arg16[0:64])
#pragma acc loop independent
			for(int i = 0 ; i < 1 ; i++) {
				arg1 [i]=i;
				arg2 [i]=i;
				arg3 [i]=i;
				arg4 [i]=i;
				arg5 [i]=i;
				arg6 [i]=i;
				arg7 [i]=i;
				arg8 [i]=i;
				arg9 [i]=i;
				arg10[i]=i;
				arg11[i]=i;
				arg12[i]=i;
				arg13[i]=i;
				arg14[i]=i;
				arg15[i]=i;
				arg16[i]=i;
			}
			gettimeofday(&tim, NULL);
			end=tim.tv_sec*1000000.0 + (tim.tv_usec);
			times[k] = ( end - start ) ;
		}
		stats (&meantime, &sd, &hm);
		printf("%d: Kernel#%d time =  %10.3f microseconds +/- %10.3f\n", n, 16, hm, CONF95*sd);


	}

}


void copyintest()
{

	int n,j,k; 
	double start,end;
	double meantime, sd, hm; 
	//  double getclock(void); 
	n=IDA;
	//printf("\n");
	//	printf("--------------------------------------------------------\n");
	//	printf("Computing COPYIN %d time\n", n); 
#pragma acc data create(btest[0:n])
	for (k=0; k<=OUTERREPS; k++){
		//	START  = GETCLOCK();
		gettimeofday(&tim, NULL);
		start=tim.tv_sec*1000000.0 + tim.tv_usec;
		//#PRAGMA ACC KERNELS COPYIN(BTEST[0:N]) 
		//#PRAGMA ACC LOOP INDEPENDENT 

#pragma acc data pcopyin(btest[0:n])
		int i ;
		//ragma acc loop independent			
		//		for (j=0; j<innerreps; j++){
		//#PRAGMA OMP PARALLEL COPYIN(BTEST) 
		//			{
		//				delay(delaylength, btest); 
		//			}     
		//		}

		gettimeofday(&tim, NULL);
		end=tim.tv_sec*1000000.0 + (tim.tv_usec);
		times[k] = ( end - start ) ;
	}


	//	stats (&meantime, &sd);

	stats (&meantime, &sd, &hm);
	//printf("%d: COPYIN time =  %10.3f microseconds +/- %10.3f\n", n, meantime, CONF95*sd);
	printf("%d: COPYIN time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95*sd);
	//	printf("COPYIN overhead =                       %10.3f microseconds +/- %10.3f\n", meantime-reftime, CONF95*(sd+refsd));

}
void copyouttest()
{

	int n,j,k; 
	double start,end;
	double meantime, sd, hm; 
	//  double getclock(void); 
	n=IDA;
	//printf("\n");
	//	printf("--------------------------------------------------------\n");
	//	printf("Computing COPYOUT %d time\n", n); 
#pragma acc data create(btest[0:n])
	for (k=0; k<=OUTERREPS; k++){
		//	START  = GETCLOCK();
		gettimeofday(&tim, NULL);
		start=tim.tv_sec*1000000.0 + tim.tv_usec;
		//#PRAGMA ACC KERNELS COPYIN(BTEST[0:N]) 
		//#PRAGMA ACC LOOP INDEPENDENT 

#pragma acc data pcopyout(btest[0:n])
		int i ;
		//ragma acc loop independent			
		//		for (j=0; j<innerreps; j++){
		//#PRAGMA OMP PARALLEL COPYIN(BTEST) 
		//			{
		//				delay(delaylength, btest); 
		//			}     
		//		}

		gettimeofday(&tim, NULL);
		end=tim.tv_sec*1000000.0 + (tim.tv_usec);
		times[k] = ( end - start ) ;
	}


	//	stats (&meantime, &sd);

	stats (&meantime, &sd, &hm);
	//	printf("%d: COPYOUT time =  %10.3f microseconds +/- %10.3f\n", n, meantime, CONF95*sd);
	printf("%d: COPYOUT time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95*sd);

	//	printf("COPYOUT overhead =                       %10.3f microseconds +/- %10.3f\n", meantime-reftime, CONF95*(sd+refsd));

}


void reductiontest()
{

	int n,j,k; 
	double start,end;
	double meantime, sd, hm; 
	double result = 0 ;
	//  double getclock(void); 
	n=IDA;
	printf("\n");
	//	printf("--------------------------------------------------------\n");
	//	printf("Computing REDUCTION %d time\n", n); 
	#pragma acc data copyin(btest[0:n])
	{
		// sum reduction
		for (k=0; k<=OUTERREPS; k++){
			gettimeofday(&tim, NULL);
			start=tim.tv_sec*1000000.0 + tim.tv_usec;

			#pragma acc kernels
			#pragma acc loop independent reduction(+:result)
			for(j=0; j < IDA; j++){
				double x = btest[j];
				result += x;
			}

			gettimeofday(&tim, NULL);
			end=tim.tv_sec*1000000.0 + (tim.tv_usec);
			times[k] = ( end - start ) ;
		}
		stats (&meantime, &sd, &hm);
		printf("%d: REDUCTION(+) time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95*sd);

		// max reduction
		for (k=0; k<=OUTERREPS; k++){
			gettimeofday(&tim, NULL);
			start=tim.tv_sec*1000000.0 + tim.tv_usec;

			#pragma acc kernels
			#pragma acc loop independent reduction(max:result)
			for(j=0; j < IDA; j++){
				double x = btest[j];
				result += x;
			}

			gettimeofday(&tim, NULL);
			end=tim.tv_sec*1000000.0 + (tim.tv_usec);
			times[k] = ( end - start ) ;
		}
		stats (&meantime, &sd, &hm);
		printf("%d: REDUCTION(max) time =  %10.3f microseconds +/- %10.3f\n", n, hm, CONF95*sd);

	}
	reftime = meantime;
	refsd = sd;  
}


void privatetest()
{
	int j,k;
	int i = 0 ; 
	double start; 
	double meantime, sd; 
	//double a[1];
	double a;
	//  double getclock(void); 

	printf("\n");
	printf("--------------------------------------------------------\n");
	printf("Computing REDUCTION time 1\n"); 

	for (k=0; k<=OUTERREPS; k++){
		start  = getclock();
		//#pragma acc kernels copyin(a) 
		//#pragma acc loop independent private(a)
		for (j=0; j<innerreps; j++){
			delay(delaylength, &a); 
			i++;	
		}
		times[k] = (getclock() - start) * 1.0e6 / (double) innerreps;
	}

	//	stats (&meantime, &sd);

	printf("PRIVATE time =                           %10.3f microseconds +/- %10.3f\n", meantime, CONF95*sd);
	printf("PRIVATE overhead =                       %10.3f microseconds +/- %10.3f\n", meantime-reftime, CONF95*(sd+refsd));

	reftime = meantime;
	refsd = sd;  
}

void stats (double *mtp, double *sdp, double *hm) 
{

	double meantime, totaltime, sumsq, mintime, maxtime, sd, cutoff; 
	double reciprocal, harmonic_mean ;
	int i, nr; 

	mintime = 1.0e10;
	maxtime = 0.;
	totaltime = 0.;

	for (i=1; i<=OUTERREPS; i++){
		mintime = (mintime < times[i]) ? mintime : times[i];
		maxtime = (maxtime > times[i]) ? maxtime : times[i];
		totaltime +=times[i];
		reciprocal += 1/times[i]; 
	} 

	meantime  = totaltime / OUTERREPS;
	harmonic_mean = OUTERREPS / reciprocal ; 
	sumsq = 0; 

	for (i=1; i<=OUTERREPS; i++){
		sumsq += (times[i]-meantime)* (times[i]-meantime); 
	} 
	sd = sqrt(sumsq/(OUTERREPS-1));

	cutoff = 3.0 * sd; 

	nr = 0; 

	for (i=1; i<=OUTERREPS; i++){
		if ( fabs(times[i]-meantime) > cutoff ) nr ++; 
	}

	//	printf("\n"); 
	//	printf("Sample_size       Average     Min         Max          S.D.          Outliers\n");
	//	printf(" %d           %10.3f   %10.3f   %10.3f    %10.3f      %d\n",OUTERREPS, meantime, mintime, maxtime, sd, nr); 
	//	printf("\n");

	*mtp = meantime; 
	*sdp = sd; 
	*hm = harmonic_mean ;
} 
