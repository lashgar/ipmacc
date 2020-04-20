/*
 *
 *      Copyright 2009-2010, STMicroelectronics, Incorporated.
 *      All rights reserved.
 *
 *        STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
 * This software is supplied under the terms of a license agreement
 * or nondisclosure agreement with STMicroelectronics and may not be
 * copied or disclosed except in accordance with the terms of that
 * agreement.
 */

/*
 * Jacobi iteration example using PGI Accelerator Directives in C
 * Build with
 *   pgcc -ta=nvidia -Minfo=accel -fast c3.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <math.h>
#include <accelmath.h>

typedef float *restrict *restrict MAT;
typedef float *restrict VEC;

void
smooth( MAT a, VEC b[100], float w0, float w1, float w2, int n, int m, int niters )
{
    int i, j, iter;
    #pragma acc region 
    {
      for( iter = 1; iter < niters; ++iter ){
	for( i = 1; i < n-1; ++i ){
	  for( j = 1; j < m-1; ++j ){
	    a[i][j] = w0 * b[i][j] + 
		  w1*(b[i-1][j] + b[i+1][j] + b[i][j-1] + b[i][j+1]) +
		  w2*(b[i-1][j-1] + b[i-1][j+1] + b[i+1][j-1] + b[i+1][j+1]);
	  }
	}
	for( i = 1; i < n-1; ++i ){
	  for( j = 1; j < m-1; ++j ){
	    b[i][j] = a[i][j];
	  }
	}
      }
    }
}

void
smoothhost( MAT a, VEC b[100], float w0, float w1, float w2, int n, int m, int niters )
{
    int i, j, iter;
    {
      for( iter = 1; iter < niters; ++iter ){
	for( i = 1; i < n-1; ++i ){
	  for( j = 1; j < m-1; ++j ){
	    a[i][j] = w0 * b[i][j] + 
		  w1*(b[i-1][j] + b[i+1][j] + b[i][j-1] + b[i][j+1]) +
		  w2*(b[i-1][j-1] + b[i-1][j+1] + b[i+1][j-1] + b[i+1][j+1]);
	  }
	}
	for( i = 1; i < n-1; ++i ){
	  for( j = 1; j < m-1; ++j ){
	    b[i][j] = a[i][j];
	  }
	}
      }
    }
}

void
doprt( char* s, MAT a, MAT ah, int i, int j )
{
    printf( "%s[%d][%d] = %g  =  %g\n", s, i, j, a[i][j], ah[i][j] );
}

int
main()
{
    MAT aa;
    VEC bb[100];
    MAT aahost;
    VEC bbhost[100];
    int i,j;
    float w0, w1, w2;
    int n, m, aerrs, berrs;
    float dif, tol;
    n = 100;
    m = 100;

    aa = (float**) malloc( sizeof(float*) * n );
    aahost = (float**) malloc( sizeof(float*) * n );
    for( i = 0; i < n; ++i ){
	aa[i] = (float*)malloc(sizeof(float) * m );
	aahost[i] = (float*)malloc(sizeof(float) * m );
    }
    bb[0] = (float*)malloc(sizeof(float) * m * 100);
    bbhost[0] = (float*)malloc(sizeof(float) * m * 100);
    for( i = 1; i < 100; ++i ){
	bb[i] = bb[i-1] + m;
	bbhost[i] = bbhost[i-1] + m;
    }
    for( i = 0; i < n; ++i ){
	for( j = 0; j < m; ++j ){
	    aa[i][j] = 0;
	    aahost[i][j] = 0;
	    bb[i][j] = i*1000 + j;
	    bbhost[i][j] = i*1000 + j;
	}
    }
    w0 = 0.5;
    w1 = 0.3;
    w2 = 0.2;
    smooth( aa, bb, w0, w1, w2, n, m, 5 );
    smoothhost( aahost, bbhost, w0, w1, w2, n, m, 5 );

    aerrs = berrs = 0;
    tol = 0.000005;
    for( i = 0; i < n; ++i ){
	for( j = 0; j < m; ++j ){
	    dif = fabsf(aa[i][j] - aahost[i][j]);
	    if( aahost[i][j] ) dif = fabsf(dif / aahost[i][j]);
	    if( dif > tol ){
		++aerrs;
		if( aerrs < 10 ){
		    printf( "aa[%d][%d] = %12.7e != %12.7e\n", i, j, (double)aa[i][j], (double)aahost[i][j] );
		}
	    }
	    dif = fabsf(bb[i][j] - bbhost[i][j]);
	    if( bbhost[i][j] ) dif = fabsf(dif / bbhost[i][j]);
	    if( dif > tol ){
		++berrs;
		if( berrs < 10 ){
		    printf( "bb[%d][%d] = %12.7e != %12.7e\n", i, j, (double)bb[i][j], (double)bbhost[i][j] );
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
