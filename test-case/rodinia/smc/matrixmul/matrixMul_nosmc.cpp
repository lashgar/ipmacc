#include <malloc.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define LEN 1024
#define SIZE LEN*LEN

#define TYPE double
#define MIN(a,b)    (a<b?a:b)


int main(int argc, char *argv[])
{
    int i;
#ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
#endif 
#ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
#endif 

    TYPE *a, *b, *c;;;
    TYPE *seq;
    a=(TYPE*)malloc(SIZE*sizeof(TYPE));
    b=(TYPE*)malloc(SIZE*sizeof(TYPE));
    c=(TYPE*)malloc(SIZE*sizeof(TYPE));
    seq=(TYPE*)malloc(SIZE*sizeof(TYPE));

    // Initialize matrices.
    for (i = 0; i < SIZE; ++i) {
        //B
        a[i] = (TYPE)i ;
        b[i] = (TYPE)2*i;
        c[i] = 0.0f;
    }// B

    unsigned long long int tic, toc;;
    // Compute vector Add
    int k,j,l;;;
    for(k=0; k<3; k++){
        printf("Calculation on GPU ... ");
        tic = clock();

        #pragma acc data pcopyin(a[0:SIZE],b[0:SIZE]) pcopy(c[0:SIZE])
        #pragma acc kernels
        #pragma acc loop independent vector(16)
        for (i = 0; i < LEN; ++i) {
            #pragma acc loop independent vector(16)
            for(j=0; j<LEN; ++j){
                TYPE sum=0;
                for (l=0; l<LEN; l+=16){
                    int offseti=l;
                    int offsetj=l;
                    {
                        if(j<LEN && i<LEN){
                            int m;
                            for(m=l; m<MIN(l+16,LEN);m++){
                                sum += a[i*LEN+m]*b[m*LEN+j];
                            }
                        }
                    }
                }
                if(j<LEN && i<LEN){
                    c[i*LEN+j] = sum;
                }
            }
        }
        toc = clock();
        printf(" %6.4f ms\n",(toc-tic)/(TYPE)1000);
    }

    // ****************
    // double-check the OpenACC result sequentially on the host
    // ****************
    // Perform the add

    printf("Calculation on CPU ... ");

    tic = clock();
    for (i = 0; i < LEN; ++i) {
        for(j=0; j<LEN; j++){
            TYPE s=0;
            for(l=0; l<LEN; l++){
                s += a[i*LEN+l]*b[l*LEN+j];
            }
            seq[i*LEN+j]=s;
            if(seq[i*LEN+j]!=c[i*LEN+j]){
                fprintf(stderr,"mismatch on %dx%d\n",i,j);
                exit(-1);
            }
        }
    }
    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(TYPE)1000);

    fprintf(stderr,"OpenACC matrix multiply test with dynamic arrays was successful!\n");

    return 0;
}
