#include <stdio.h>
#define N 1000000

int main(void) {
    double pi = 0.0f; long i;
//#pragma acc parallel loop reduction(+:pi)
    #pragma acc kernels
    #pragma acc loop independent reduction(+:pi)
    for (i=0; i<N; i++) {
        double t= (double)((i+0.5)/N);
        pi +=4.0/(1.0+t*t);
    }
    printf("pi=%16.15f\n",pi/N);
    return 0;
}
