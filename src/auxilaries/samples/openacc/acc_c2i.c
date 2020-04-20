#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <math.h>
#include <openacc.h>
#include <accelmath.h>

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

int main( int argc, char* argv[] )
{
    int n;      /* size of the vector */
    float *a;  /* the vector */
    float *restrict r;  /* the results */
    float *e;  /* expected results */
    float s, c;
    timestruct t1, t2, t3;
    long long cgpu, chost;
    int i;
    if( argc > 1 )
	n = atoi( argv[1] );
    else
	n = 1000000;
    if( n <= 0 ) n = 1000000;

    a = (float*)malloc(n*sizeof(float));
    r = (float*)malloc(n*sizeof(float));
    e = (float*)malloc(n*sizeof(float));
    for( i = 0; i < n; ++i ) a[i] = (float)(i+1) * 2.0f;
    acc_init( acc_device_nvidia );

    gettime( &t1 );
    #pragma acc kernels loop
    for( i = 0; i < n; ++i ){
	s = sinf(a[i]);
	c = cosf(a[i]);
	r[i] = s*s + c*c;
    }
    gettime( &t2 );
    cgpu = usec(t1,t2);
    for( i = 0; i < n; ++i ){
	s = sinf(a[i]);
	c = cosf(a[i]);
	e[i] = s*s + c*c;
    }
    gettime( &t3 );
    chost = usec(t2,t3);
    /* check the results */
    for( i = 0; i < n; ++i )
	assert( fabsf(r[i] - e[i]) < 0.000001f );
    printf( "%13d iterations completed\n", n );
    printf( "%13ld microseconds on GPU\n", cgpu );
    printf( "%13ld microseconds on host\n", chost );
    return 0;
}
