#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

int main( int argc, char* argv[] )
{
    int n;      /* size of the vector */
    float *a;  /* the vector */
    float *restrict r;  /* the results */
    float *e;  /* expected results */
    int i;
    if( argc > 1 )
        n = atoi( argv[1] );
    else
        n = 100000;
    if( n <= 0 ) n = 100000;

    a = (float*)malloc(n*sizeof(float));
    r = (float*)malloc(n*sizeof(float));
    e = (float*)malloc(n*sizeof(float));
    /* initialize */
    for( i = 0; i < n; ++i ) a[i] = (float)(i+1);

    #pragma acc kernels loop
    for( i = 0; i < n; ++i ) r[i] = a[i]*2.0f;
    /* compute on the host to compare */
    for( i = 0; i < n; ++i ) e[i] = a[i]*2.0f;
    /* check the results */
    for( i = 0; i < n; ++i )
        assert( r[i] == e[i] );
    printf( "%d iterations completed\n", n );
    return 0;
}
