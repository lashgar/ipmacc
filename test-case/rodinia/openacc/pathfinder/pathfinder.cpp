#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include <string.h>
#include "timer.h"

void run(int argc, char** argv);

/* define timer macros */
#define pin_stats_reset()   startCycle()
#define pin_stats_pause(cycles)   stopCycle(cycles)
#define pin_stats_dump(cycles)    printf("timer: %Lu\n", cycles)

//#define DUMPOUT

int rows, cols;
int* data;
#define wall(i,j) (data[i*cols+j])
int* result;
#define M_SEED 9

void
init(int argc, char** argv)
{
    if(argc==3){
        cols = atoi(argv[1]);
        rows = atoi(argv[2]);
    }else{
        printf("Usage: pathfiner width num_of_steps\n");
        exit(0);
    }
    data = new int[rows*cols];
    result = new int[cols];

    assert(data && result);
    //int seed = M_SEED;
    //srand(seed);

    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            wall(i,j) = (i+j + i*j) % 100;
        }
    }
    for (int j = 0; j < cols; j++)
        result[j] = wall(0,j);
#ifdef DUMPOUT
        for (int i = 0; i < rows; i++)
        {
            for (int j = 0; j < cols; j++)
            {
                printf("%d ",wall(i,j)) ;
            }
            printf("\n") ;
        }
#endif
}

    void 
fatal(char *s)
{
    fprintf(stderr, "error: %s\n", s);

}

#define IN_RANGE(x, min, max)   ((x)>=(min) && (x)<=(max))
#define CLAMP_RANGE(x, min, max) x = (x<(min)) ? min : ((x>(max)) ? max : x )
#define MIN(a, b) ((a)<=(b) ? (a) : (b))

int main(int argc, char** argv)
{
#ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
#endif 
#ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
#endif 




    run(argc,argv);

    return EXIT_SUCCESS;
}

void run(int argc, char** argv)
{
    init(argc, argv);

    unsigned long long cycles;

    int *src, *dst, *temp;
    int min;

    dst = result;
    src = new int[cols];
    //memset(src, 0, sizeof(int)*cols);
    //memset(data, 0, sizeof(int)*rows*cols);

    pin_stats_reset();
    //#pragma acc data copyin(src[0:cols],data[0:rows*cols]) copyout(dst[0:cols])
    #pragma acc data copy(src[0:cols],data[0:rows*cols],dst[0:cols])
    {
        int t;
        for ( t = 0; t < rows-1; t++) {
            temp = src;
            src = dst;
            dst = temp;
            #pragma acc kernels
            #pragma acc loop private(min) independent
            for(int n = 0; n < cols; n++){
                min = src[n];
                if (n > 0)
                    min = MIN(min, src[n-1]);
                if (n < cols-1)
                    min = MIN(min, src[n+1]);
                // dst[n] = wall(t+1,n)+min;
                dst[n] =  (data[(t+1)*cols+n]) + min ;
            }
        }
    }
    /* end pragma acc data */

    pin_stats_pause(cycles);
    pin_stats_dump(cycles);

#ifdef DUMPOUT

    //    for (int i = 0; i < cols; i++)
    //
    //            printf("%d ",data[i]) ;
    //
    //    printf("\n") ;

    for (int i = 0; i < cols; i++){
        printf("%d ",dst[i]) ;
        if((i%10)==9){
            printf("\n");
        }
    }
    printf("\n") ;

#endif

    delete [] data;
    delete [] dst;
    delete [] src;
}

