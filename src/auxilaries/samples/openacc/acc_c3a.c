/*
 *      Copyright 2009-2012, STMicroelectronics, Incorporated.
 *      All rights reserved.
 *
 *        STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
 * This software is supplied under the terms of a license agreement
 * or nondisclosure agreement with STMicroelectronics and may not be
 * copied or disclosed except in accordance with the terms of that
 * agreement.
 */

/*
 * Jacobi iteration example using OpenACC in C
 * Build with
 *   pgcc -acc -Minfo=accel -fast c3.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <openacc.h>
#include <math.h>

#if defined(_WIN32) || defined(_WIN64)
#include <sys/timeb.h>
#define gettime(a) _ftime(a)
#define usec(t1,t2) ((((t2).time-(t1).time)*1000+((t2).millitm-(t1).millitm))*100)
typedef struct _timeb timestruct;
#else
#include <sys/time.h>
#define gettime(a) gettimeofday(a,NULL)
#define usec(t1,t2) (((t2).tv_sec-(t1).tv_sec)*1000000+((t2).tv_usec-(t1).tv_usec))
typedef struct timeval timestruct;
#endif

void
smooth( float*restrict a, float*restrict b, float w0, float w1, float w2, int n, int m, int niters )
{
    int i, j, iter;
    float* tmp;
    for( iter = 1; iter <= niters; ++iter ){
	#pragma acc kernels loop present(b[0:n*m],a[0:n*m]) independent
	for( i = 1; i < n-1; ++i ){
	    for( j = 1; j < m-1; ++j ){
		a[i*m+j] = w0 * b[i*m+j] + 
		    w1*(b[(i-1)*m+j] + b[(i+1)*m+j] + b[i*m+j-1] + b[i*m+j+1]) +
		    w2*(b[(i-1)*m+j-1] + b[(i-1)*m+j+1] + b[(i+1)*m+j-1] + b[(i+1)*m+j+1]);
		}
	}
	tmp = a;  a = b;  b = tmp;
    }
}

void
smoothhost( float*restrict a, float*restrict b, float w0, float w1, float w2, int n, int m, int niters )
{
    int i, j, iter;
    float* tmp;
    for( iter = 1; iter <= niters; ++iter ){
	for( i = 1; i < n-1; ++i ){
	    for( j = 1; j < m-1; ++j ){
		a[i*m+j] = w0 * b[i*m+j] + 
		    w1*(b[(i-1)*m+j] + b[(i+1)*m+j] + b[i*m+j-1] + b[i*m+j+1]) +
		    w2*(b[(i-1)*m+j-1] + b[(i-1)*m+j+1] + b[(i+1)*m+j-1] + b[(i+1)*m+j+1]);
		}
	}
	tmp = a;  a = b;  b = tmp;
    }
}

void
doprt( char* s, float*restrict a, float*restrict ah, int i, int j, int n, int m )
{
    printf( "%s[%d][%d] = %g  =  %g\n", s, i, j, a[i*m+j], ah[i*m+j] );
}

int
main( int argc, char* argv[] )
{
    float *aa, *bb, *aahost, *bbhost;
    int i,j;
    float w0, w1, w2;
    int n, m, aerrs, berrs, iters;
    float dif, rdif, tol;
    timestruct t1, t2, t3;
    long long cgpu, chost;

    n = 0;
    m = 0;
    iters = 0;

    if( argc > 1 ){
	n = atoi( argv[1] );
	if( argc > 2 ){
	    m = atoi( argv[2] );
	    if( argc > 3 ){
		iters = atoi( argv[3] );
		if( argc > 4 ){
		    if( !strcmp( argv[4], "host" ) ||
			!strcmp( argv[4], "HOST" ) ){
			acc_set_device( acc_device_host );
			printf( "using host\n" );
		    }else
		    if( !strcmp( argv[4], "nvidia" ) ||
			!strcmp( argv[4], "NVIDIA" ) ){
			acc_set_device( acc_device_nvidia );
			acc_init( acc_device_nvidia );
			printf( "using nvidia\n" );
		    }else{
			printf( "unknown device: %s\nUsing default\n", argv[4] );
		    }
		}
	    }
	}
    }

    if( n <= 0 ) n = 100;
    if( m <= 0 ) m = n;
    if( iters <= 0 ) iters = 10;

    aa = (float*) malloc( sizeof(float) * n * m );
    aahost = (float*) malloc( sizeof(float) * n * m );
    bb = (float*)malloc( sizeof(float) * n * m );
    bbhost = (float*)malloc( sizeof(float) * n * m );
    for( i = 0; i < n; ++i ){
	for( j = 0; j < m; ++j ){
	    aa[i*m+j] = 0;
	    aahost[i*m+j] = 0;
	    bb[i*m+j] = i*1000 + j;
	    bbhost[i*m+j] = i*1000 + j;
	}
    }
    w0 = 0.5;
    w1 = 0.3;
    w2 = 0.2;
    gettime( &t1 );
    #pragma acc data copy(bb[0:n*m],aa[0:n*m])
    {
    smooth( aa, bb, w0, w1, w2, n, m, iters );
    }
    gettime( &t2 );
    smoothhost( aahost, bbhost, w0, w1, w2, n, m, iters );
    gettime( &t3 );

    cgpu = usec(t1,t2);
    chost = usec(t2,t3);

    printf( "matrix %d x %d, %d iterations\n", n, m, iters );
    printf( "%13ld microseconds optimized\n", cgpu );
    printf( "%13ld microseconds on host\n", chost );

    aerrs = berrs = 0;
    tol = 0.000005;
    for( i = 0; i < n; ++i ){
	for( j = 0; j < m; ++j ){
	    rdif = dif = fabsf(aa[i*m+j] - aahost[i*m+j]);
	    if( aahost[i*m+j] ) rdif = fabsf(dif / aahost[i*m+j]);
	    if( rdif > tol ){
		++aerrs;
		if( aerrs < 10 ){
		    printf( "aa[%d][%d] = %12.7e != %12.7e, dif=%12.7e\n", i, j, (double)aa[i*m+j], (double)aahost[i*m+j], (double)dif );
		}
	    }
	    rdif = dif = fabsf(bb[i*m+j] - bbhost[i*m+j]);
	    if( bbhost[i*m+j] ) rdif = fabsf(dif / bbhost[i*m+j]);
	    if( rdif > tol ){
		++berrs;
		if( berrs < 10 ){
		    printf( "bb[%d][%d] = %12.7e != %12.7e, dif=%12.7e\n", i, j, (double)bb[i*m+j], (double)bbhost[i*m+j], (double)dif );
		}
	    }
	}
    }
    if( aerrs == 0 && berrs == 0 ){
	printf( "no errors found\n" );
	return 0;
    }else{
	printf( "%d ERRORS found\n", aerrs + berrs );
	return 1;
    }
}
